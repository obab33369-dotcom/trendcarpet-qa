#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Path injection
REFORMA_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REFORMA_DIR / "orchestrator"))

try:
    import db as orchestrator_db
except ImportError:
    orchestrator_db = None

def main():
    parser = argparse.ArgumentParser(
        description="Query the Claude CLI (Claude Code) programmatically using standard settings."
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="The prompt query to send to Claude."
    )
    parser.add_argument(
        "--task-id", "-t",
        type=str,
        required=True,
        help="The Task ID associated with this query."
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="sonnet",
        help="The model to use (e.g., 'sonnet', 'opus', 'fable'). Default: 'sonnet'."
    )
    parser.add_argument(
        "--permission-mode", "-p",
        type=str,
        default="plan",
        choices=["plan", "dontAsk", "bypassPermissions", "acceptEdits", "default", "auto"],
        help="Permission mode for the session. Default: 'plan'."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print verbose execution details."
    )

    args = parser.parse_args()

    # Create task directory for attempts and inputs/outputs
    task_dir = REFORMA_DIR / ".reforma" / "tasks" / args.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    brief_file = task_dir / "brief.md"
    response_file = task_dir / "response.md"
    usage_ledger = task_dir / "usage.json"
    attempts_journal = task_dir / "attempts.md"
    
    # Save the current prompt as brief.md
    with open(brief_file, "w", encoding="utf-8") as f:
        f.write(args.prompt)

    # Build the command using absolute path to native binary
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        # Fallback to PATH resolution
        native_path = "claude"

    cmd = [
        native_path,
        "--print",
        "--model", args.model,
        "--permission-mode", args.permission_mode,
        "--output-format", "json",
        "--tools", "Read,Grep,Glob"  # Enforce read-only for filesystem (no Edit/Write/Bash)
    ]

    if args.verbose:
        print(f"Executing: {' '.join(cmd)}", file=sys.stderr)

    try:
        env = os.environ.copy()
        # Ensure ANTHROPIC_API_KEY is not in env to force team prenu / OAuth flow
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]

        # If a previous session exists for this task, we can try to resume it.
        # However, Fable 5 recommends starting fresh across attempts.
        # We can implement that in the orchestrator side.

        res = subprocess.run(
            cmd,
            input=args.prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            env=env,
            shell=(sys.platform == 'win32')
        )

        if res.returncode == 0:
            try:
                # Parse JSON output from Claude
                output_json = json.loads(res.stdout)
                result_text = output_json.get("result", "")
                session_id = output_json.get("session_id", "")
                total_cost = output_json.get("total_cost_usd", 0.0)
                usage = output_json.get("usage", {})
                
                # Write response text to response.md
                with open(response_file, "w", encoding="utf-8") as f:
                    f.write(result_text)
                    
                # Save usage telemetry
                telemetry = {
                    "session_id": session_id,
                    "cost_usd": total_cost,
                    "usage": usage,
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(usage_ledger, "w", encoding="utf-8") as f:
                    json.dump(telemetry, f, indent=2)
                    
                # Print result text to stdout
                sys.stdout.write(result_text)
                
                # Record to global ledger in sqlite database if accessible
                if orchestrator_db is not None:
                    try:
                        orchestrator_db.add_ledger_entry(
                            args.task_id,
                            session_id,
                            usage.get("input_tokens", 0),
                            usage.get("output_tokens", 0),
                            total_cost
                        )
                    except Exception as ex:
                        if args.verbose:
                            print(f"Warning: failed to write to database ledger: {ex}", file=sys.stderr)
                
                sys.exit(0)
                
            except json.JSONDecodeError:
                print("Error: Failed to parse Claude CLI JSON output.", file=sys.stderr)
                print(f"RAW STDOUT:\n{res.stdout}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Claude CLI exited with code {res.returncode}", file=sys.stderr)
            if res.stdout:
                print(f"STDOUT:\n{res.stdout}", file=sys.stderr)
            if res.stderr:
                print(f"STDERR:\n{res.stderr}", file=sys.stderr)
            sys.exit(res.returncode)

    except Exception as e:
        print(f"Error executing Claude CLI: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
