import subprocess
import sys
import os

def main():
    # Configure stdout and stderr to use UTF-8 to prevent charmap encoding errors on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    prompt = """Today's date is June 12, 2026.
We are refining the collaborative developer loop design for REFORMA.
Here is our feedback and some follow-up questions/points we want to discuss with you (Claude Opus):

1. **Objection on Raw Diffs**: Applying raw unified diffs programmatically (via git apply or patch) can be very fragile, especially on Windows due to CRLF vs LF line endings, tab/space indentations, and encoding issues. 
   - Instead of raw diffs, what if Claude writes the *complete proposed file* or *fully updated class/function blocks* to a structured JSON envelope or dedicated files under `.reforma/tasks/<task-id>/proposed/`? How would you structure this so Antigravity can apply it robustly without regex failures?
   
2. **FastAPI MCP Server Specification**: You suggested turning our FastAPI panel into an MCP server for Claude.
   - What specific MCP tools should this server expose? 
   - How can Claude use these tools during a `/diagnose` session to inspect logs, current file lock states, or triage metrics?
   
3. **Loop Guard & Cost Budgeting**: 
   - What is a practical mechanism for the `Claude-Bridge` subagent to track token costs and count API usage in real-time? (e.g. parsing Claude Code's JSON output or tracking locally?)
   
4. **Git Integration**: We agree with initializing Git. Should we automate branch creation for each task (e.g., `task/<task-id>`) so that Antigravity can test changes in isolation and discard them if they fail tests, before merging to main?

Please refine your proposed architecture based on these points.
"""

    # Build the command using absolute path to native binary
    native_path = os.path.expanduser(r"~\.local\bin\claude.exe")
    if not os.path.exists(native_path):
        print("Error: claude.exe not found at default location.")
        sys.exit(1)

    cmd = [
        native_path,
        "--print",
        "--model", "opus",
        "--permission-mode", "plan",
        "--tools", "Read"
    ]

    print("Sending follow-up request to Claude Opus...")
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]

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
        print("\n=== CLAUDE OPUS FOLLOW-UP RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()
