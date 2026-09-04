import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from .git_manager import run_process_in_job

logger = logging.getLogger("orchestrator.session")

SESSION_BASE_DIR = Path(r"C:\rf\session")

def _find_key_recursive(d, target_key):
    if not isinstance(d, dict):
        return None
    if target_key in d:
        return d[target_key]
    for k, v in d.items():
        if isinstance(v, dict):
            res = _find_key_recursive(v, target_key)
            if res is not None:
                return res
        elif isinstance(v, list):
            for item in v:
                res = _find_key_recursive(item, target_key)
                if res is not None:
                    return res
    return None

def write_mcp_config(task_id: str, bearer_token: str) -> Path:
    """
    Writes a task-specific .mcp.json configuration file outside the worktree.
    """
    config_dir = SESSION_BASE_DIR / task_id
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / ".mcp.json"
    
    mcp_config = {
        "mcpServers": {
            "reforma": {
                "url": "http://127.0.0.1:8765/mcp/sse",
                "headers": {
                    "Authorization": f"Bearer {bearer_token}"
                }
            }
        }
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=2)
        
    logger.info(f"Wrote MCP config for task {task_id} to {config_path}")
    return config_path

def write_attempts_journal(task_id: str, attempts_journal: str):
    """
    Writes/updates the attempts journal inside the session directory.
    """
    config_dir = SESSION_BASE_DIR / task_id
    config_dir.mkdir(parents=True, exist_ok=True)
    journal_path = config_dir / "attempts.md"
    
    with open(journal_path, "w", encoding="utf-8") as f:
        f.write(attempts_journal)
    logger.info(f"Updated attempts journal for task {task_id}")

def launch_session(
    repo_path: Path,
    task_id: str,
    worktree_path: Path,
    bearer_token: str,
    brief: str,
    attempts_journal: str = None,
    max_turns: int = 30
) -> dict:
    """
    Launches Claude CLI (Opus 4.8) at MAX effort in the task's worktree.
    Streams stdout to parse cost and turn metrics.
    """
    # 1. Setup session files
    mcp_config_path = write_mcp_config(task_id, bearer_token)
    if attempts_journal:
        write_attempts_journal(task_id, attempts_journal)
        
    # Build defense-in-depth settings.json (deny filesystem write & shell tools)
    settings_dir = worktree_path / ".claude"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_path = settings_dir / "settings.json"
    settings_content = {
        "allowedTools": [
            "Read",
            "Grep",
            "Glob",
            "mcp__reforma__*"
        ]
    }
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings_content, f, indent=2)

    # 2. Build the command
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        native_path = "claude" # fallback to PATH
        
    cmd = [
        str(native_path),
        "--print",
        "--model", "opus",
        "--permission-mode", "plan",
        "--tools", "Read,Grep,Glob",
        "--mcp-config", str(mcp_config_path),
        "--max-turns", str(max_turns),
        "--verbose",
        "--output-format", "stream-json"
    ]
    
    # 3. Clean environment (unset key for Web Team Auth routing)
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]
    env["CLAUDE_CODE_EFFORT_LEVEL"] = "max"
    
    logger.info(f"Spawning Claude Opus session for task {task_id} in {worktree_path}")
    
    # Complete prompt content
    full_prompt = brief
    if attempts_journal:
        full_prompt = f"{brief}\n\n=========================================\nHISTORY OF PRIOR ATTEMPTS (attempts.md):\n=========================================\n{attempts_journal}"
        
    # Spawn in job object
    import subprocess
    proc = run_process_in_job(
        cmd,
        cwd=str(worktree_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE
    )
    
    # Write prompt to stdin
    try:
        proc.stdin.write(full_prompt.encode("utf-8"))
        proc.stdin.close()
    except Exception:
        pass
        
    # Stream and parse stream-json output using a background thread to prevent blocking
    import time
    import queue
    import threading
    
    def _read_stream_to_queue(stream, q):
        try:
            for line in iter(stream.readline, b""):
                q.put(line)
        except Exception as e:
            q.put(e)
        finally:
            q.put(None)
            
    q = queue.Queue()
    t = threading.Thread(target=_read_stream_to_queue, args=(proc.stdout, q), daemon=True)
    t.start()
    
    start_time = time.monotonic()
    
    is_waiting_for_test = False
    test_wait_start = 0.0
    total_test_wait = 0.0
    
    stdout_chunks = []
    total_cost = 0.0
    turn_count = 0
    raw_response_text = ""
    stop_reason = "completed"
    
    while True:
        # Check active wall-clock time breaker (15 min active agent time)
        now = time.monotonic()
        active_time = (now - start_time) - total_test_wait
        if is_waiting_for_test:
            active_time -= (now - test_wait_start)
            
        if active_time >= 900.0:  # 15 minutes
            logger.warning(f"Wall-clock session breaker tripped ({active_time:.1f}s active agent time). Terminating process.")
            stop_reason = "walltime_kill"
            proc.kill()
            break
            
        # Check cost breaker ($5)
        if total_cost >= 5.0:
            logger.warning(f"Cost session breaker tripped (${total_cost:.2f} >= $5.00). Terminating process.")
            stop_reason = "cost_kill"
            proc.kill()
            break
            
        # Read from queue without blocking indefinitely
        try:
            line = q.get(timeout=1.0)
        except queue.Empty:
            if proc.poll() is not None:
                # Process exited and no more output to read
                break
            continue
            
        if line is None:
            # EOF reached
            break
            
        if isinstance(line, Exception):
            logger.error(f"Error reading stdout: {line}")
            break
            
        line_str = line.decode("utf-8", errors="ignore").strip()
        if not line_str:
            continue
            
        stdout_chunks.append(line_str)
            
        try:
            msg = json.loads(line_str)
            if isinstance(msg, dict):
                # Robustly find cost in nested payload
                cost_usd = _find_key_recursive(msg, "total_cost_usd")
                if cost_usd is not None:
                    total_cost = float(cost_usd)
                else:
                    cost_val = _find_key_recursive(msg, "cost")
                    if cost_val is not None:
                        total_cost = float(cost_val)
                
                # Robustly find turns in nested payload
                turns_val = _find_key_recursive(msg, "num_turns")
                if turns_val is not None:
                    turn_count = int(turns_val)
                elif msg.get("type") == "turn_start":
                    turn_count += 1
                
                # Extract raw response text
                delta = msg.get("delta")
                if isinstance(delta, dict) and "text" in delta:
                    raw_response_text += delta["text"]
                elif "text" in msg and isinstance(msg["text"], str):
                    raw_response_text += msg["text"]
                elif msg.get("type") == "text" and isinstance(msg.get("content"), str):
                    raw_response_text += msg["content"]
                elif msg.get("type") == "text" and isinstance(msg.get("text"), str):
                    raw_response_text += msg["text"]
                    
                # Track test waiting logic
                tool_name = _find_key_recursive(msg, "name")
                if tool_name and isinstance(tool_name, str):
                    if "run_tests" in tool_name or "get_test_result" in tool_name or "mcp__reforma" in tool_name:
                        is_waiting_for_test = True
                        test_wait_start = time.monotonic()
                
                # If we get a response, a new turn, or a tool result while waiting for a test, stop waiting
                if is_waiting_for_test:
                    has_res = False
                    if "result" in msg or "tool_result" in msg:
                        has_res = True
                    elif msg.get("type") in ("text", "turn_start", "assistant", "message"):
                        has_res = True
                    if has_res:
                        total_test_wait += time.monotonic() - test_wait_start
                        is_waiting_for_test = False
        except Exception:
            # If it's not valid JSON, treat it as raw stdout text
            raw_response_text += line_str + "\n"
            
    # Read remaining stderr
    stderr_out = proc.stderr.read().decode("utf-8", errors="ignore")
    proc.wait()
    
    # Cleanup job object handle
    if hasattr(proc, 'h_job'):
        import win32api
        win32api.CloseHandle(proc.h_job)
        
    success = (proc.returncode == 0) and (stop_reason == "completed")
    
    logger.info(f"Claude session finished with exit code {proc.returncode}. Cost: ${total_cost:.4f}, Turns: {turn_count}, Stop Reason: {stop_reason}")
    if not success:
        logger.error(f"Claude session failed with stderr:\n{stderr_out}")
        try:
            diag_path = SESSION_BASE_DIR / task_id / "diag_run.log"
            with open(diag_path, "w", encoding="utf-8") as df:
                df.write("=== STDOUT ===\n")
                df.write("\n".join(stdout_chunks))
                df.write("\n\n=== STDERR ===\n")
                df.write(stderr_out)
            logger.info(f"Wrote session diagnostics to {diag_path}")
        except Exception as diag_ex:
            logger.error(f"Failed to write session diagnostics: {diag_ex}")
    
    return {
        "success": success,
        "exit_code": proc.returncode,
        "cost": total_cost,
        "turns": turn_count,
        "text": raw_response_text,
        "stderr": stderr_out,
        "stop_reason": stop_reason
    }
