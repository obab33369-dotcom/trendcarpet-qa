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
We have implemented Loop 1 (Modules 1-5) containing the SQLite database, Git worktree isolation, changeset validations, FastAPI MCP server, and ask_claude bridge script.

As Fable 5, evaluating at the absolute MAX effort/reasoning capacity:
1. Please read the following files in the workspace using your Read tool:
   - `orchestrator/db.py`
   - `orchestrator/git_manager.py`
   - `orchestrator/changeset.py`
   - `scripts/ask_claude.py`
   - `interior-designer-automation/app.py` (specifically the MCP server portion at the bottom of the file)
2. Review the code thoroughly and identify any bugs, logic errors, or corner cases (especially regarding Windows NTFS, win32 process tree Job Objects, FastAPI ASGI event loop blocking, or SQLite transactions).
3. Output a detailed list of bugs/issues found, followed by the exact code corrections we should apply.
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
        "--tools", "Read"  # Allow Fable 5 to read files in the repository
    ]

    print("Sending Loop 1 Review request to Claude Fable 5 at MAX effort...")
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
        print("\n=== CLAUDE FABLE 5 LOOP 1 REVIEW RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()
