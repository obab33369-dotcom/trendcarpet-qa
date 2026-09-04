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
We have applied all of your second-round corrections (Loop 2), including:
1. Importing the orchestrator db module in ask_claude.py to use `add_ledger_entry` instead of direct unconfigured sqlite queries (resolving H1).
2. Implementing the exact `_is_within` containment check using Path.relative_to inside changeset.py to resolve the H2 prefix bypass vulnerability.
3. Hardening run_process_in_job in git_manager.py to prevent handle leaks and using exact-subtree path checks in cleanup_worktree (resolving M3).
4. Dropping the unsupported `--test` argument from the orchestrator subprocess exec call in app.py.

As Fable 5, evaluating at the absolute MAX effort/reasoning capacity:
1. Please read the updated files in the workspace using your Read tool:
   - `orchestrator/db.py`
   - `orchestrator/git_manager.py`
   - `orchestrator/changeset.py`
   - `scripts/ask_claude.py`
   - `interior-designer-automation/app.py` (specifically the MCP server portion at the bottom of the file)
2. Run a third design and code review to verify that all previous issues (both Loop 1 and Loop 2) are fully resolved.
3. Confirm if the code is now 100% robust, safe, and ready to be delivered.
4. Output your final verdict and review notes.
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

    print("Sending Loop 3 Review request to Claude Fable 5 at MAX effort...")
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
        print("\n=== CLAUDE FABLE 5 LOOP 3 REVIEW RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()
