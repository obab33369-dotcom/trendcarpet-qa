import subprocess
import sys
import os

def main():
    # Configure stdout/stderr for UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    prompt = """Today's date is June 12, 2026.
We are designing a collaborative developer loop for our project REFORMA.
We have applied all of your previous design and code suggestions from the first review, including:
1. Enabling WAL mode, busy timeout, and foreign keys in SQLite db.py.
2. Simplifying the run_process_in_job handle management in git_manager.py to prevent process and thread handle leaks.
3. Adding atomic git rollback (git reset --hard) to apply_changeset in changeset.py.
4. Making the long-polling get_test_result, submit_changeset, and run_tests MCP tools asynchronous in app.py to prevent blocking the FastAPI ASGI event loop.

As Fable 5, evaluating at the absolute MAX effort/reasoning capacity:
1. Please read the updated files in the workspace using your Read tool:
   - `orchestrator/db.py`
   - `orchestrator/git_manager.py`
   - `orchestrator/changeset.py`
   - `scripts/ask_claude.py`
   - `interior-designer-automation/app.py` (specifically the MCP server portion at the bottom of the file)
2. Verify that our fixes are fully correct and resolved all previously identified bugs.
3. Check for any remaining edge cases, subtle concurrency bugs, or new issues introduced by these fixes.
4. Output your detailed feedback and any final code corrections.
"""

    # Build the command using absolute path to native binary
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        print("Error: claude.exe not found.")
        sys.exit(1)

    cmd = [
        native_path,
        "--print",
        "--model", "fable",
        "--permission-mode", "plan",
        "--tools", "Read"
    ]

    print("Sending Loop 2 Review request to Claude Fable 5 at MAX effort...")
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]
    
    # Configure MAX effort level for Fable 5
    env["CLAUDE_CODE_EFFORT_LEVEL"] = "max"

    res = subprocess.run(
        cmd,
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='ignore',
        env=env,
        shell=(sys.platform == 'win32')
    )

    if res.returncode == 0:
        print("\n=== CLAUDE FABLE 5 LOOP 2 REVIEW RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()
