import os
import sys
import time
import json
import re
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from orchestrator import db as orchestrator_db
from orchestrator import git_manager as orchestrator_git
from orchestrator import session_runner as orchestrator_session
from orchestrator import attempts as orchestrator_attempts
from orchestrator import test_gate as orchestrator_test_gate

logger = logging.getLogger("orchestrator.driver")

def build_clean_env(extra_vars: dict = None) -> dict:
    allow_keys = {
        "PATH", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT",
        "TEMP", "TMP", "LANG", "LC_ALL", "USERPROFILE", "USERNAME",
        "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING", "PYTHONPATH"
    }
    clean_env = {}
    for k, v in os.environ.items():
        k_upper = k.upper()
        if k_upper in allow_keys or k_upper.startswith("PYTHON") or k_upper.startswith("REFORMA_"):
            clean_env[k] = v
            
    if extra_vars:
        clean_env.update(extra_vars)
        
    return clean_env

def capture_baseline(worktree_path: Path, base_commit: str, task_id: str) -> list:
    python_exe = sys.executable
    nodeids_out = orchestrator_session.SESSION_BASE_DIR / task_id / "nodeids_base.json"
    nodeids_out.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepend runner_plugins to PYTHONPATH
    plugins_dir = str(Path(__file__).resolve().parent / "runner_plugins")
    python_path = plugins_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
    
    extra_vars = {
        "REFORMA_OFFLINE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "REFORMA_NODEID_OUT": str(nodeids_out),
        "PYTHONPATH": python_path
    }
    env = build_clean_env(extra_vars)
            
    cmd = [python_exe, "-m", "pytest", "--co", "-q", "-p", "no:cacheprovider", "-p", "reforma_offline_guard", "tests/"]
    
    try:
        proc = orchestrator_git.run_process_in_job(cmd, cwd=str(worktree_path), env=env)
        proc.wait(timeout=60)
        if nodeids_out.exists():
            with open(nodeids_out, "r", encoding="utf-8") as f:
                node_ids = json.load(f)
                orchestrator_db.record_node_baseline(base_commit, node_ids)
                return node_ids
    except Exception as e:
        logger.error(f"Failed to capture baseline nodeids: {e}")
    return []

def verify_worktree(worktree_path: Path, task_id: str, base_commit: str) -> dict:
    python_exe = sys.executable
    nodeids_out = orchestrator_session.SESSION_BASE_DIR / task_id / "nodeids_attempt.json"
    nodeids_out.parent.mkdir(parents=True, exist_ok=True)
    
    plugins_dir = str(Path(__file__).resolve().parent / "runner_plugins")
    python_path = plugins_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
    
    extra_vars = {
        "REFORMA_OFFLINE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "REFORMA_NODEID_OUT": str(nodeids_out),
        "REFORMA_TASK_ID": task_id,
        "PYTHONPATH": python_path
    }
    env = build_clean_env(extra_vars)
            
    cmd = [
        python_exe, "-m", "pytest", "-q",
        "-p", "no:cacheprovider",
        "-p", "reforma_offline_guard",
        "-m", "not online", "tests/"
    ]
    
    logger.info(f"Running verification tests in {worktree_path}")
    proc = None
    try:
        proc = orchestrator_git.run_process_in_job(
            cmd,
            cwd=str(worktree_path),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = proc.communicate(timeout=600)
        returncode = proc.returncode
        output = (stdout_data.decode("utf-8", errors="ignore") or "") + (stderr_data.decode("utf-8", errors="ignore") or "")
    except Exception as e:
        returncode = -1
        output = f"Exception running verification: {e}"
    finally:
        if proc and hasattr(proc, "h_job"):
            import win32api
            win32api.CloseHandle(proc.h_job)
            
    digest = orchestrator_test_gate.digest_pytest_output(output)
    
    weakened = False
    if returncode == 0:
        touched_files = []
        try:
            target_branch = orchestrator_git.get_target_branch(worktree_path)
            # Find the merge base between HEAD and the target branch
            mb_proc = subprocess.run(
                ["git", "merge-base", "HEAD", target_branch],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                check=True
            )
            merge_base = mb_proc.stdout.strip()
            
            diff_proc = subprocess.run(
                ["git", "diff", "--name-only", merge_base],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                check=True
            )
            touched_files = [line.strip() for line in diff_proc.stdout.splitlines() if line.strip()]
        except Exception as e:
            logger.warning(f"Failed to get touched files: {e}")
            
        is_clean = orchestrator_test_gate.check_weakening(
            task_id, base_commit, str(nodeids_out), touched_files
        )
        if not is_clean:
            weakened = True
            
    return {
        "success": (returncode == 0) and not weakened,
        "returncode": returncode,
        "weakened": weakened,
        "output": output,
        "digest": digest
    }

def check_breakers(task_id: str) -> str:
    task = orchestrator_db.get_task(task_id)
    if not task:
        return "CONTINUE"
        
    spend = task.get("spend_usd", 0.0)
    if spend >= 10.0:
        logger.warning(f"Cost task breaker tripped: spend ${spend:.2f} >= $10.00.")
        return "ESCALATE_COST"
        
    attempts = task.get("attempts_count", 0)
    if attempts >= 3:
        logger.warning(f"Consecutive failed attempts breaker tripped: {attempts} >= 3.")
        return "ESCALATE_ATTEMPTS"
        
    changesets = orchestrator_db.get_changesets_for_task(task_id)
    patch_counts = {}
    for cs in changesets:
        pid = cs["patch_id"]
        if pid == "unknown":
            continue
        patch_counts[pid] = patch_counts.get(pid, 0) + 1
        if patch_counts[pid] >= 2:
            logger.warning(f"Identical-diff breaker tripped: patch_id {pid} repeated 2x.")
            return "ESCALATE_IDENTICAL_DIFF"
            
    signatures = orchestrator_db.get_recent_attempt_signatures(task_id, 4)
    sig_seen = set()
    for sig in signatures:
        p_id = sig["patch_id"]
        f_sig = sig["failing_signature"]
        if p_id == "unknown" or not f_sig:
            continue
        combo = (p_id, f_sig)
        if combo in sig_seen:
            logger.warning(f"Oscillation breaker tripped: combination {combo} repeated.")
            return "ESCALATE_OSCILLATION"
        sig_seen.add(combo)
        
    # Fallback: Check if failing_signature is exactly the same 3 times in a row
    if len(signatures) >= 3:
        sigs_to_check = [sig.get("failing_signature") for sig in signatures[:3]]
        if len(set(sigs_to_check)) == 1 and sigs_to_check[0] and sigs_to_check[0] != "":
            logger.warning(f"Oscillation breaker tripped: failing signature '{sigs_to_check[0]}' repeated 3x consecutively.")
            return "ESCALATE_OSCILLATION"
        
    today = datetime.now().strftime("%Y-%m-%d")
    daily_spend = orchestrator_db.get_daily_spend(today)
    if daily_spend >= 75.0:
        logger.warning(f"Daily global spend breaker tripped: spend ${daily_spend:.2f} >= $75.00.")
        return "PAUSE_DAILY_SPEND"
        
    conn = orchestrator_db.get_db_connection()
    cursor = conn.cursor()
    one_hour_ago = datetime.isoformat(datetime.fromtimestamp(time.time() - 3600))
    cursor.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE status IN ('FAILED', 'ESCALATED') AND updated_at >= ?
    """, (one_hour_ago,))
    recent_fails = cursor.fetchone()[0]
    conn.close()
    
    if recent_fails >= 5:
        logger.warning(f"Global task failures breaker tripped: {recent_fails} failures in last hour.")
        return "PAUSE_GLOBAL_FAILURES"
        
    return "CONTINUE"

def run_canary(repo_path: Path, last_known_good_commit: str) -> bool:
    task_id = "canary-test"
    try:
        worktree_path = orchestrator_git.create_worktree(repo_path, task_id, last_known_good_commit)
        res = verify_worktree(worktree_path, task_id, last_known_good_commit)
        orchestrator_git.cleanup_worktree(repo_path, task_id)
        return res["success"]
    except Exception as e:
        logger.error(f"Canary check crashed: {e}")
        return False

class Driver:
    def __init__(self, repo_path: Path, bearer_token: str, poll_interval: float = 5.0):
        self.repo_path = repo_path
        self.bearer_token = bearer_token
        self.poll_interval = poll_interval
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def run_forever(self):
        self.running = True
        logger.info("REFORMA Developer Loop Driver started.")
        while self.running:
            try:
                if orchestrator_db.is_loop_paused():
                    time.sleep(self.poll_interval)
                    continue
                    
                self.tick()
            except Exception as e:
                logger.exception(f"Exception in driver tick: {e}")
            time.sleep(self.poll_interval)
            
    def stop(self):
        self.running = False
        self.executor.shutdown(wait=False)
        
    def tick(self):
        # 1. Process PENDING tasks
        conn = orchestrator_db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'PENDING'")
        pending_tasks = [dict(r) for r in cursor.fetchall()]
        conn.close()
        
        for task in pending_tasks:
            self.process_pending_task(task)
            
        # 2. Process QUEUED tasks
        conn = orchestrator_db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'QUEUED'")
        queued_tasks = [dict(r) for r in cursor.fetchall()]
        conn.close()
        
        for task in queued_tasks:
            self.drain_queued_task(task)
            
        # 3. Reclaim stale ASSIGNED tasks
        conn = orchestrator_db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'ASSIGNED'")
        assigned_tasks = [dict(r) for r in cursor.fetchall()]
        conn.close()
        
        for task in assigned_tasks:
            updated_at_str = task.get("updated_at")
            if updated_at_str:
                try:
                    updated_at = datetime.fromisoformat(updated_at_str)
                    diff = (datetime.now() - updated_at).total_seconds()
                    if diff > 1200:  # 20 minutes
                        task_id = task["task_id"]
                        logger.warning(f"Reaper: Task {task_id} has been ASSIGNED for {diff/60:.1f} minutes. Reverting to PENDING.")
                        orchestrator_db.update_task_status_cas(task_id, "ASSIGNED", "PENDING")
                except Exception as reaper_err:
                    logger.error(f"Reaper: Failed to parse updated_at '{updated_at_str}' for task {task.get('task_id')}: {reaper_err}")

    def process_pending_task(self, task: dict):
        task_id = task["task_id"]
        if not orchestrator_db.update_task_status_cas(task_id, "PENDING", "ASSIGNED"):
            return
        logger.info(f"Driver intake: Enqueueing task {task_id} into ThreadPoolExecutor.")
        self.executor.submit(self._run_session_async, task)

    def _run_session_async(self, task: dict):
        task_id = task["task_id"]
        base_commit = task["base_commit"]
        
        logger.info(f"Driver background task worker: Processing task {task_id} at base commit {base_commit}")
        
        try:
            breaker = check_breakers(task_id)
            if breaker != "CONTINUE":
                self.handle_breaker_trip(task_id, breaker)
                return
                
            worktree_path = None
            try:
                worktree_path = orchestrator_git.create_worktree(self.repo_path, task_id, base_commit)
            except Exception as e:
                logger.error(f"Failed to create worktree for {task_id}: {e}")
                orchestrator_db.update_task_status(task_id, "ESCALATED")
                return
                
            capture_baseline(worktree_path, base_commit, task_id)
            
            brief_path = Path(r"C:\rf\session") / task_id / "brief.txt"
            brief = "Fix the issues and verify using pytest."
            if brief_path.exists():
                try:
                    brief = brief_path.read_text(encoding="utf-8").strip()
                except Exception:
                    pass
                    
            attempts_journal = orchestrator_attempts.build_attempts_journal(task_id)
            max_turns = 50 if "large" in task_id.lower() else 30
            
            session_res = orchestrator_session.launch_session(
                self.repo_path,
                task_id,
                worktree_path,
                self.bearer_token,
                brief,
                attempts_journal=attempts_journal,
                max_turns=max_turns
            )
            
            session_id = f"sess_{int(time.time())}"
            cost = session_res.get("cost", 0.0)
            orchestrator_db.add_ledger_entry(task_id, session_id, 0, 0, cost)
            today = datetime.now().strftime("%Y-%m-%d")
            orchestrator_db.add_daily_spend(today, cost)
            
            stop_reason = session_res.get("stop_reason", "completed")
            if not session_res.get("success", False) or stop_reason != "completed":
                err_sig = stop_reason if stop_reason != "completed" else f"session_fail_exit_{session_res.get('exit_code')}"
                logger.warning(f"Task {task_id} session failed: {err_sig}")
                attempts_count = orchestrator_db.increment_task_attempts(task_id)
                hypothesis = orchestrator_attempts.extract_hypothesis(session_res.get("text", ""))
                
                orchestrator_attempts.log_attempt(
                    task_id,
                    attempts_count,
                    patch_id="unknown",
                    changed_files=[],
                    failing_signature=err_sig,
                    hypothesis=hypothesis
                )
                
                breaker = check_breakers(task_id)
                if breaker != "CONTINUE":
                    self.handle_breaker_trip(task_id, breaker)
                else:
                    orchestrator_db.update_task_status(task_id, "PENDING")
            else:
                current_task = orchestrator_db.get_task(task_id)
                if current_task and current_task.get("status") == "ASSIGNED":
                    logger.warning(f"Task {task_id} session finished successfully but state remains ASSIGNED (no tests queued). Reverting to PENDING.")
                    orchestrator_db.update_task_status_cas(task_id, "ASSIGNED", "PENDING")
        except Exception as e:
            logger.exception(f"Unhandled exception in background task worker for task {task_id}: {e}")
            orchestrator_db.update_task_status(task_id, "ESCALATED")

    def drain_queued_task(self, task: dict):
        task_id = task["task_id"]
        base_commit = task["base_commit"]
        
        if not orchestrator_db.update_task_status_cas(task_id, "QUEUED", "REBASING"):
            return
            
        logger.info(f"Driver drain: Rebasing and verifying task {task_id}")
        
        def verify_func(worktree_path: Path) -> bool:
            res = verify_worktree(worktree_path, task_id, base_commit)
            return res["success"]
            
        rebase_res = orchestrator_git.rebase_and_verify(self.repo_path, task_id, verify_func)
        
        if rebase_res == "READY_FOR_REVIEW":
            orchestrator_db.update_task_status_cas(task_id, "REBASING", "READY_FOR_REVIEW")
            logger.info(f"Task {task_id} is successfully READY_FOR_REVIEW!")
            try:
                orchestrator_git.cleanup_worktree(self.repo_path, task_id)
            except Exception as e:
                logger.warning(f"Failed to cleanup worktree for task {task_id}: {e}")
        elif rebase_res == "CONFLICT":
            orchestrator_db.update_task_status_cas(task_id, "REBASING", "ESCALATED")
            logger.error(f"Task {task_id} rebase conflicted. Moved to ESCALATED.")
            try:
                orchestrator_git.cleanup_worktree(self.repo_path, task_id)
            except Exception as e:
                logger.warning(f"Failed to cleanup worktree for task {task_id}: {e}")
        else:
            attempts_count = orchestrator_db.increment_task_attempts(task_id)
            
            orchestrator_attempts.log_attempt(
                task_id,
                attempts_count,
                patch_id="rebase_fail",
                changed_files=[],
                failing_signature="verify_failed_after_rebase",
                hypothesis="Code diverged from target tip during rebase."
            )
            
            breaker = check_breakers(task_id)
            if breaker != "CONTINUE":
                self.handle_breaker_trip(task_id, breaker)
            else:
                orchestrator_db.update_task_status_cas(task_id, "REBASING", "PENDING")

    def handle_breaker_trip(self, task_id: str, breaker: str):
        if breaker.startswith("ESCALATE"):
            logger.error(f"Breaker {breaker} tripped for task {task_id}. Escalating task.")
            orchestrator_db.update_task_status(task_id, "ESCALATED")
        elif breaker == "PAUSE_DAILY_SPEND":
            logger.critical("Daily spend breaker tripped. Pausing loop.")
            orchestrator_db.set_loop_paused(True, reason="Daily spend limit ($75) reached.")
        elif breaker == "PAUSE_GLOBAL_FAILURES":
            logger.critical("Global failures breaker tripped. Pausing loop and running canary.")
            orchestrator_db.set_loop_paused(True, reason="High task failure rate (>=5/hour) detected.")
            target_branch = orchestrator_git.get_target_branch(self.repo_path)
            run_canary(self.repo_path, target_branch)
