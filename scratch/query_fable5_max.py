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
We previously ran a design review query with Claude Fable 5 at the default "High" effort setting.
Here is the design review response that Fable 5 generated:

============================================================
FABLE 5 (HIGH EFFORT) DESIGN REVIEW RESPONSE:
============================================================

1. **Race & Deadlock Analysis**
   - Apply the changeset inside the Git worktree checked out at `base_commit`. There the `base_sha256` check is deterministic (it only fails if Claude misreported what it read — a real integrity error worth hard-failing on). Staleness relative to main is handled by rebasing the task branch onto current main, re-running tests, then merging. Cap rebase-retest retries at 2 before escalating.
   - Use a single serialized merge queue to handle semantic merge conflicts.
   - Make `run_tests` an asynchronous job: it returns a `job_id` immediately, and Claude polls `get_test_result(job_id)` to prevent blocking the FastAPI event loop.
   - Use TTL leases (owner PID + TTL + heartbeat) instead of bare locks for lock management.
   - Kill the full child process tree (`taskkill /T /F` on Windows) before removing Git worktrees to prevent file locks.
   - Avoid file watching; trigger only via `submit_changeset` MCP call.

2. **Loop Stability & Circuit Breakers**
   - Max turns per Claude session: 30 (50 for large tasks).
   - Max consecutive failed attempts: 3.
   - Identical-diff detector: Max 2x repeats of normalized diff hash.
   - Oscillation detector: Reject if any file returns to a previously-seen content hash.
   - Cost per session: $5 hard kill.
   - Cost per task: $10.
   - Daily global cap: $75.
   - Wall clock per session/task: 15 min / 60 min.
   - Global Breaker: >=5 task failures within 1 hour pauses the loop (protects against broken environment).

3. **Context Efficiency**
   - Hybrid session strategy: Use `--resume` within one fix cycle (cheap and retains memory). Start fresh/stateless across attempts (after breaker trip or when changing strategy).
   - Use an `attempts.md` journal in each task folder containing previous failed attempts to prevent stateless retries from repeating the same fixes.
   - Run with `--output-format stream-json` to get per-message token/cost telemetry.

4. **Permission Blast Radius**
   - Enforce read-only at the harness: Deny `Edit`/`Write` globally in `.claude/settings.json`, allowing writes only under `.reforma/tasks/**`.
   - No general Bash in allowlist: Scope it to specific commands (`Bash(pytest *)`) or use MCP `run_tests`.
   - Server-side changeset validation: Reject absolute paths, `..` segments, normalize Windows separators, and deny writes to `.git/**`, `.claude/**`, `.github/workflows/**`, and shell profiles.
   - Low-privilege account execution: Run the headless Claude process under a low-privilege user with no credentials in its env.

5. **Routing Economics**
   - Antigravity handles high-volume/shallow tasks (search, log parsing, formatting, template code generation).
   - Claude Code handles deep tasks (architecture decisions, multi-file refactoring, auth/security code, debugging complex errors).
   - Human handles policy/licensing, migrations, and circuit-breaker escalations.

============================================================

As Fable 5, evaluating at the absolute MAX effort/reasoning capacity:
1. Do you agree with this analysis and the proposed guidelines/circuit breakers?
2. Did this high-effort analysis miss any significant aspects, subtle edge cases, or potential failure points (especially regarding Windows environments, local concurrency, or LLM-specific behaviors)?
3. Please refine the recommendations and provide your absolute final decisions and optimization suggestions at MAX effort.
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

    print("Sending MAX effort request to Claude Fable 5...")
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
        print("\n=== CLAUDE FABLE 5 MAX RESPONSE ===")
        print(res.stdout)
    else:
        print(f"\nError: Claude CLI exited with code {res.returncode}")
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()
