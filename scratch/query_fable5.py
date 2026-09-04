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
We are designing a collaborative developer loop for our project REFORMA.
Here is the refined architecture plan proposed by Claude Opus:

============================================================
REFORMA Agentic Developer Loop Design
============================================================

1. **Structured "Change Set" Envelope (Single-Writer)**
   - Antigravity (Gemini) owns all writes to the repository. Claude Code operates as a read-only reasoning oracle by default.
   - Claude Code writes proposed changes to `.reforma/tasks/<task-id>/proposed/` (mirroring the repo path structure).
   - Claude Code also writes `.reforma/tasks/<task-id>/changeset.json` with the following structure:
     ```json
     {
       "task_id": "T-2026-0612-auth-fix",
       "base_commit": "a1b2c3d",
       "operations": [
         {
           "op": "modify",
           "path": "src/services/auth.py",
           "base_sha256": "<hash of file Claude actually read>",
           "proposed_file": "proposed/src/services/auth.py",
           "eol": "lf",
           "encoding": "utf-8",
           "bom": false
         }
       ]
     }
     ```
   - Before applying any write, Antigravity hashes the current working-tree file and compares it with `base_sha256` (optimistic concurrency control). If they mismatch, the change set is rejected.

2. **FastAPI MCP Server**
   - Exposes tools to Claude Code: `get_logs`, `list_locks`, `get_triage_metrics`, `list_tasks`, `run_tests`, `submit_changeset`, etc.
   - Mounted in the same FastAPI process running on port 8001.

3. **Git Worktree Isolation**
   - For every task, a dedicated branch `reforma/task/<task-id>` and a dedicated worktree `.reforma/work/<task-id>` are created.
   - Changes are applied and tests are run in isolation in the worktree. Successful runs are merged to main; failing ones are discarded immediately.

4. **Loop Guard & Cost Budgeting**
   - Real-time token usage and cost are parsed from `claude --output-format json` output.
   - Safeguards: Max turns per run, repeated-edit detector, wall-clock timeout, and daily/per-task cost caps.

============================================================

As Fable 5, the high-reasoning model, we want you to review this architecture and make final decisions on guidelines, limits, and safety measures. Specifically:

1. **Race & Deadlock Analysis**: In this single-writer, headless model, what race conditions or deadlocks (where Antigravity and Claude Code are waiting on each other) could still occur, and how do we prevent them?
2. **Loop Stability & Circuit Breakers**: Concretely, what specific thresholds should we set to prevent infinite edit loops or cost runaway?
   - Max Claude turns per session?
   - Max consecutive test failures before human escalation?
   - Cost budget per task?
3. **Context Efficiency**: Is this file-based brief/response pattern optimal, or is there a better way to pass context (like using `--resume` sessions vs stateless calls)? Where is context most likely to get lost?
4. **Permission Blast Radius**: We plan to pre-approve an allowlist in `.claude/settings.json` for headless runs. What is the worst-case scenario if a prompt is hijacked or tool execution misfires? What safeguards should we enforce?
5. **Routing Economics**: Which classes of tasks should stay entirely in Antigravity (cheap/large token pool) vs. when should we escalate to Claude Code, and when to a Human?
6. **Observability & Log Schema**: What minimal logging schema do we need to easily debug loop failures and cost runaways?

Please give us your expert assessment and recommendations.
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

    print("Sending request to Claude Fable 5...")
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
        print("\n=== CLAUDE FABLE 5 RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()
