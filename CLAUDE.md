# REFORMA Developer Loop — Architecture & Operating Contract (CLAUDE.md)

> This file is the canonical contract every loop session re-reads. It governs the
> autonomous developer loop ("Antigravity 2.0") that runs Claude as a coding agent
> against this repository on local Windows. Authoritative over prompt instructions.

## 0. Repo facts & hard prerequisites

- **Platform:** Windows 11, PowerShell. Paths are case-insensitive (NTFS).
- **Default/target branch:** `master` (the loop detects it dynamically — NEVER hardcode `main`).
- **PREREQUISITE — baseline commit:** the loop uses `git worktree`, which requires a
  HEAD commit. This repo currently has none. Before any loop run, commit a baseline
  on `master`. No commit ⇒ no worktrees ⇒ no loop.
- **Worktree root:** `C:\rf\wt\<task-id>` (short path to dodge MAX_PATH).
- **Session config root:** `C:\rf\session\<task-id>\` (OUTSIDE the worktree).
- `core.longpaths=true` and `gc.auto=0` are set on the repo by the orchestrator.
- **Claude Model Alias Mapping:** In the source code (e.g., `session_runner.py` and `query_opus.py`), the parameter `"--model" "opus"` is passed to the Claude CLI. In the project's documentation and comments, this model is consistently referred to as Claude Opus 4.8 (or Opus 4.8). By using the `--model opus` flag in the command, you are invoking the model that in this project is referred to as Claude Opus 4.8.

## 1. Agent ground rules (the contract)

- The agent is **read-only on the filesystem.** Allowed tools: `Read, Grep, Glob` plus
  the REFORMA MCP tools. No `Edit`, `Write`, or `Bash`. Code changes are proposed ONLY
  as a `submit_changeset` payload.
- The agent operates inside its **task worktree** (its `cwd`). All reads, hashes, and
  proposed edits reference that immutable snapshot at `base_commit`.
- The agent MUST NOT modify (server-enforced denylist): `.git/**`, `.claude/**`,
  `.github/**`, `.reforma/**`, `orchestrator/**`, `interior-designer-automation/**`,
  `reforma-turboflow/**` controller code it isn't tasked with, PowerShell profiles,
  dependency lockfiles, or test configuration (`pytest.ini`, `pyproject.toml [tool.pytest]`,
  `conftest.py`, `tests/**`) without a human-review flag.
- Bug-fix tasks MUST add/keep a test that fails at `base_commit` and passes on the fix.
  A green run that *removed or weakened* red tests is NEVER a success (see §4 gate).

## 2. Loop architecture

### 2.1 Components
- **Dev-loop process** = `orchestrator/mcp_server.py` (NEW). One process that:
  (a) serves the MCP tools, (b) runs the **driver** as a startup background task,
  (c) holds the single in-process **git lock**. Bound to `127.0.0.1:8765`. Imports
  NONE of the cookie/Playwright code.
- **Driver** (background task in the dev-loop process): intake → pinned session →
  changeset → tests → breaker decision → enqueue → rebase-and-verify → ready-for-review.
- **Session runner** = `orchestrator/session_runner.py` (NEW): launches the Claude CLI
  in a Job Object with `cwd` = worktree.
- **Verifier**: the offline `pytest` suite (§4), run server-side via `run_tests`.
- **Merge drainer**: `git_manager.rebase_and_verify` (REWRITE of `serialized_rebase_and_merge`).
- **State**: `orchestrator/db.py` (SQLite, WAL/FK/busy_timeout).
- **Cookie/Playwright app** = `interior-designer-automation/app.py`: stays a SEPARATE
  process. The MCP mount is REMOVED from it.

### 2.2 State machine (SQLite `tasks.status`)
```
PENDING ──driver picks up, creates worktree, launches session──▶ ASSIGNED
ASSIGNED ──submit_changeset applied OK──▶ (agent calls run_tests) ──▶ TESTING
TESTING  ──tests green──▶ QUEUED
TESTING  ──tests red / apply fail──▶ ASSIGNED (attempts++, retry)  [breaker→FAILED/ESCALATED]
QUEUED   ──drainer: rebase clean + verify green──▶ READY_FOR_REVIEW   (LOOP STOPS HERE)
QUEUED   ──rebase conflict──▶ ESCALATED
QUEUED   ──verify red after rebase──▶ ASSIGNED (attempts++)
READY_FOR_REVIEW ──human approves & merges──▶ MERGED
any ──breaker trip──▶ ESCALATED ; unrecoverable ──▶ FAILED
```
Add `REBASING`, `READY_FOR_REVIEW` to the CHECK constraint (the DB has no production
data — recreate tables in `init_db`).

### 2.3 Worktree-pinning flow (the prerequisite)
1. Driver: under git lock, `create_worktree(repo, task_id, target_tip)` → `C:\rf\wt\<id>`.
2. Driver: write `C:\rf\session\<id>\.mcp.json` (bearer token) and seed `attempts.md`.
3. Driver: spawn Claude CLI (Job Object, stripped env) with `cwd` = the worktree.
4. Agent reads/greps/globs the worktree, computes `base_sha256` over **bytes-on-disk**,
   submits a changeset.
5. `submit_changeset` validates+applies **to that same existing worktree** (it does NOT
   create one). OCC is now integrity-only: a hash mismatch means the agent misreported.
6. A committed `.gitattributes` (`* text=auto eol=lf`) keeps CRLF from diverging hashes.

### 2.4 Serialized rebase-and-verify (merge process)
One global git lock; one task validated at a time. In the task's OWN worktree:
1. `target_tip = git rev-parse <target>`.
2. `git -C <worktree> rebase <target>`. Conflict ⇒ `rebase --abort` ⇒ `ESCALATED`.
3. Run the §4 verify command in the rebased worktree. Red ⇒ back to `ASSIGNED` (attempt++).
4. Green ⇒ `READY_FOR_REVIEW`. **The loop stops. It never touches your checked-out branch.**
5. Human merges approved branches: `git merge --no-ff reforma/task/<id>`.
- NEVER run `git checkout`/`git merge` in the primary working tree.
- All `.git` mutations (worktree add/remove, rebase) go through the single git lock.
- **Post-soak evolution only:** auto-merge small diffs on allowlisted paths by
  fast-forwarding a dedicated `reforma/integration` branch you don't check out (via
  `git update-ref`), never the branch in your primary tree.

### 2.5 Circuit breakers (monotonic clock; lease liveness checked before takeover)
| Guard | Threshold | On trip |
|---|---|---|
| Max turns / session | 30 (50 if task tagged `large`) | end session; driver decides retry vs escalate by `stop_reason` |
| Consecutive failed attempts / task | 3 | ESCALATED + `attempts.md` |
| Identical-diff | `git patch-id --stable` repeats 2× | ESCALATED |
| Oscillation | same (patch-id, failing-test signature) recurs | ESCALATED |
| Cost / session | $5 hard kill (from stream-json `total_cost_usd`) | count as failed attempt |
| Cost / task | $10 | ESCALATED |
| Wall clock / session | 15 min **active agent time** (exclude test waits) | kill + failed attempt |
| Daily global | $75 (alert 80%) | pause loop |
| Global breaker | ≥5 task failures / hour | pause loop + run canary (verify at last-known-good) to classify env-vs-agent |

### 2.6 attempts.md (harness-written, ~4 KB, last 4 attempts)
Per attempt: number, changeset `patch-id`, changed files, failing-test signature
(names + first traceback frame), one-line hypothesis. Fresh sessions get this in the
brief so they don't re-propose attempt #1. Within a fix cycle use `--resume`; start
fresh across attempts or past ~150k context tokens.

### 2.7 Idempotency & crash recovery
- `changeset_id = sha256(canonical payload)`; duplicate submit returns the existing
  attempt (no double-apply, no double `attempts_count`).
- On startup: reap `RUNNING` jobs → `FAILED`; prune orphan worktrees; return a
  structured "unknown job" for stale `job_id`s so the agent re-submits.
- Cap concurrent test jobs at 1/worktree, ~2 global. Check a disk-space floor before
  creating worktrees. Janitor sweeps orphan worktrees/logs.

## 3. Security boundary

### 3.1 Process split (the critical change)
- REMOVE `app.mount("/mcp", mcp.sse_app())` from `interior-designer-automation/app.py`.
- The MCP tools + git/db/changeset modules live in `orchestrator/mcp_server.py`, which
  imports nothing from the cookie/Playwright app. Code that the agent can influence must
  never share a process with `get_browser_cookies()`.

### 3.2 Bind + bearer auth
- Bind uvicorn to `127.0.0.1:8765` only.
- On startup, generate a random bearer token; write it to `C:\rf\session\token` (0600-ish
  ACL) and into each task's `C:\rf\session\<id>\.mcp.json`. An ASGI middleware rejects any
  `/mcp` request lacking `Authorization: Bearer <token>`.
- `.mcp.json` lives OUTSIDE the worktree; the CLI is launched with `--mcp-config <that path>`.
  The token is NEVER placed in any child process env.

### 3.3 Test-runner isolation
- pytest runs in a Job Object child with a **stripped env**: `GEMINI_API_KEY` removed,
  no bearer token, `REFORMA_OFFLINE=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`,
  `PYTHONPATH` prepended with `orchestrator/runner_plugins` (outside the worktree).
- **Phase-3 hardening (strongly recommended):** run the test runner as a low-privilege
  local Windows account (`reforma-runner`) with no read access to your Chrome/Edge profile
  or `C:\rf\session\`, or inside Windows Sandbox.

### 3.4 Path canonicalization fixes (`changeset.canonicalize_path`)
- Normalize each path part with `.rstrip(" .")` before the denylist compare (defeats
  `.github.` ≡ `.github`).
- Reject any part matching `~\d` (8.3 short-name aliases like `GITHUB~1`).
- Keep existing containment, ADS (`:`), reserved-name, and denylist checks; apply denylist
  case-insensitively to the normalized parts.

### 3.5 Other guards
- **Test-weakening gate** (§4) — server-side, not bypassable by the agent.
- **Lockfile-only installs**: the loop never auto-installs from agent-edited manifests;
  manifest/lockfile changes require human review.
- **Secret scan + size limit** on every changeset; reject writes to `.reforma/**` itself.
- Never use `--dangerously-skip-permissions`.

## 4. Offline verification command spec

**Pinned command (run server-side, in the worktree, Job Object, 600s timeout):**
```
python -m pytest -q -p no:cacheprovider -p reforma_offline_guard -m "not online" tests/
```
- `tests/` layout: `tests/test_smoke.py` (deliberate imports of pure modules — NOT the
  cookie app, NOT modules with heavy import-time side effects), `tests/test_triage.py`
  (golden fixtures in `tests/fixtures/` for `triage.verify_turboflow_outputs`: valid +
  malformed `rooms_turboflow.json` / `turboflow_ready.csv`), `tests/test_changeset.py`
  (security regressions: path traversal, `.github.`, `GITHUB~1`, ADS, OCC mismatch).
- Anything needing network/browser/Gemini is marked `@pytest.mark.online` and excluded.
- `reforma_offline_guard` is a pytest plugin in `orchestrator/runner_plugins/` (OUTSIDE the
  worktree, agent cannot edit). It (a) monkeypatches `socket` to block non-loopback connects,
  and (b) records the collected node-id set to a runner-controlled file.
- **Reward-hacking gate:** the driver compares the attempt's collected node-id set to the
  `base_commit` set. If the set shrank, or the changeset touched `tests/**`/`conftest.py`/
  `pytest.ini`/`pyproject.toml [tool.pytest]`, the run is flagged for human review and
  CANNOT auto-count as success.
- Output is digested server-side (failed names + first traceback frames + tail); full logs
  fetchable by reference via `get_logs(tail, grep)`.

## 5. Concrete code changes (step-by-step)

### Phase 0 — Prerequisites
1. `git add -A && git commit -m "baseline"` on `master` (worktrees require a commit).
2. Add `.gitattributes`: `* text=auto eol=lf`.
3. Add `.gitignore` entries: `.mcp.json`, `C:\rf\` artifacts are external anyway.
4. `git config gc.auto 0`. (longpaths already set by `init_git_settings`.)
5. (Phase-3) create the `reforma-runner` low-priv account + ACLs.

### `orchestrator/changeset.py`
- In `canonicalize_path`, before the `forbidden_dirs` check, normalize parts:
  `norm = part.rstrip(" .").lower()`; reject if `norm` in `{".git",".claude",".github",".reforma"}`
  or if `re.search(r"~\d", part)`.

### `orchestrator/git_manager.py`
- Add `get_target_branch(repo)`: detect default (`git symbolic-ref --quiet refs/remotes/origin/HEAD`,
  else current branch); return `master` here. Replace ALL hardcoded `"main"` (lines ~189/190/196/216/217).
- REWRITE `serialized_rebase_and_merge` → `rebase_and_verify(repo, task_id, verify_func)` per §2.4:
  rebase **in the task worktree**, verify there, return `READY|CONFLICT|VERIFY_FAILED`. Do NOT
  `git checkout`/`merge` in the primary tree. Remove the `_merge` worktree dance.
- Add a module-level git lock; wrap worktree add/remove/rebase. Call `git config gc.auto 0` in `init_git_settings`.

### `orchestrator/db.py`
- Add `REBASING`, `READY_FOR_REVIEW` to the `tasks.status` CHECK (recreate tables; no prod data).
- Add `changesets(changeset_id PK, task_id, patch_id, created_at)` for idempotency + patch-id breakers.
- Add a `meta` row for the global merge lock / daily-spend window. Store breaker timestamps as epoch
  (monotonic-friendly), not ISO, to survive hibernate.

### `interior-designer-automation/app.py`
- DELETE the MCP mount (`app.mount("/mcp", …)`) and the `@mcp.tool()` dev-loop handlers. This file
  reverts to the cookie/Playwright app only.

### `orchestrator/mcp_server.py` (NEW)
- FastAPI + uvicorn bound to `127.0.0.1:8765`; bearer ASGI middleware (§3.2).
- Move the MCP tools here: `submit_changeset`, `run_tests`, `get_test_result`, `get_logs`,
  `get_triage_metrics`. Changes:
  - `submit_changeset`: do NOT call `create_worktree`; assert the worktree exists and apply there
    (fixes OCC inversion). Compute `changeset_id`; return existing attempt on duplicate.
  - `run_tests` / `run_tests_background`: replace `cmd = [python_exe, "-m", "pytest"]` with the §4
    pinned command + stripped offline env.
- `@app.on_event("startup")`: `init_db()`, crash recovery (§2.7), launch the driver background task.
- Single in-process git lock shared by tools + driver.

### `orchestrator/session_runner.py` (NEW)
- Launch the Claude CLI via `run_process_in_job` with `cwd` = worktree and:
  `--allowedTools "Read Grep Glob mcp__reforma__*"`, `--mcp-config C:\rf\session\<id>\.mcp.json`,
  `--max-turns 30`, `--output-format stream-json`, a `--settings` denylist (no Edit/Write/Bash),
  NEVER `--dangerously-skip-permissions`. Parse stream-json for live `total_cost_usd` (cost breaker).
  Write `attempts.md` entries (§2.6).

### `orchestrator/driver.py` (NEW, run as the startup background task)
- Intake `PENDING` → worktree → `.mcp.json` + `attempts.md` → session. Watch task status; on
  `QUEUED` run `rebase_and_verify`; apply breakers; populate `attempts.md`; resume-vs-fresh policy.

### `orchestrator/runner_plugins/reforma_offline_guard.py` (NEW)
- pytest plugin: block non-loopback sockets; record collected node-ids for the test-weakening gate.

## 6. Phased roadmap

- **Phase 0 — Prerequisites:** baseline commit, `.gitattributes`, `.gitignore`, `gc.auto=0`.
  *Gate:* `git worktree add` succeeds against `master`.
- **Phase 1 — Make it runnable:** target-branch detection; `submit_changeset` stops creating
  worktrees; `session_runner.py` with `--cwd`/`--max-turns`/`stream-json`/`--mcp-config`; `.mcp.json`;
  swap hardcoded pytest for the §4 command; stand up a minimal `tests/` (smoke + one triage fixture).
  *Gate:* a hand-fed task produces a worktree-pinned session whose changeset applies and whose
  offline verify runs green/red deterministically; OCC mismatch is integrity-only.
- **Phase 2 — The brain:** `mcp_server.py` process split + bearer; `driver.py`; `rebase_and_verify`;
  state-machine transitions; breakers; idempotency; `attempts.md`; crash recovery.
  *Gate:* end-to-end PENDING→READY_FOR_REVIEW with a real fix; breakers trip on a stuck task;
  a duplicate submit is idempotent; restart recovers cleanly.
- **Phase 3 — Hardening:** path-bypass fixes; offline guard + network block; test-weakening gate;
  secret scan + size limit; lockfile-only installs; low-priv runner / Windows Sandbox.
  *Gate:* attempts to write `.github.`/`GITHUB~1`/network/secret-exfil/test-deletion are all blocked.
- **Phase 4 — Soak:** human-approves ALL merges; two weeks of telemetry; tune thresholds.
- **Phase 5 — Selective autonomy:** auto-merge small diffs on allowlisted paths via a dedicated
  `reforma/integration` fast-forward (never your checked-out branch).
