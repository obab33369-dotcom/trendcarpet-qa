# Implementation Plan

Antigravity 2.0 — Phase 2 ("The brain") completion. This plan covers the six
remaining features and is authoritative against `CLAUDE.md`. It is grounded in the
current code state:

- `orchestrator/db.py` — schema already has `REBASING`/`READY_FOR_REVIEW` in the
  `tasks` CHECK, plus `changesets` and `meta` tables. Helpers exist for tasks,
  changesets, meta, ledger. **No breaker/daily-window helpers yet.**
- `orchestrator/mcp_server.py` — serves MCP tools, has `auth_middleware`,
  `run_crash_recovery`, and a `startup_event`. **The driver is NOT launched.**
  `run_tests_background` runs pytest **without** `-p reforma_offline_guard` and
  **without** the node-id gate.
- `orchestrator/session_runner.py` — `launch_session()` spawns the CLI in a Job
  Object, parses `total_cost_usd`/turns from stream-json, and already has
  `write_attempts_journal()`. **No attempts.md generation logic and no live
  cost/turn/wall-clock kill.**
- `orchestrator/git_manager.py` — `rebase_and_verify()`, `create_worktree()`,
  `cleanup_worktree()`, module-level `git_lock` all exist.
- `orchestrator/changeset.py` — path canonicalization hardening already done.
- `orchestrator/runner_plugins/` — **does not exist.**
- `tests/` — `test_smoke.py`, `test_changeset.py` exist. No `test_triage.py`,
  no `tests/fixtures/`.

Implementation order is dependency-driven: **Feature 2 (offline guard)** and the
**DB helpers** unblock everything else, then **Feature 3 (breakers)**, **Feature 5
(test-weakening gate)**, **Feature 4 (attempts.md)**, **Feature 1 (driver)**, and
finally **Feature 6 (integration)**.

---

## Feature 0 (prerequisite) — DB helper additions

These helpers are consumed by the breakers, the gate, and the driver. Add to
`orchestrator/db.py`. No schema migration needed beyond one new table (no prod data;
`init_db` recreates).

### 0.1 New table: `node_id_baselines`
Used by the test-weakening gate (§5) to compare an attempt's collected pytest node-id
set against the `base_commit` set.

```sql
CREATE TABLE IF NOT EXISTS node_id_baselines (
    base_commit TEXT PRIMARY KEY,
    node_ids    TEXT NOT NULL,   -- JSON array of node-id strings
    created_at  REAL NOT NULL
);
```

### 0.2 Helper functions
- `record_node_baseline(base_commit: str, node_ids: list[str])` — `INSERT OR REPLACE`.
- `get_node_baseline(base_commit: str) -> list[str] | None` — JSON-decode or `None`.
- `count_patch_id(task_id, patch_id) -> int` — `SELECT count(*) FROM changesets WHERE task_id=? AND patch_id=?` (identical-diff breaker).
- `get_recent_attempt_signatures(task_id, n=4) -> list[dict]` — join `changesets` +
  latest `jobs.result_payload` to assemble `(patch_id, failing_test_signature)` tuples
  for the oscillation breaker and `attempts.md`.
- `add_job_meta(job_id, key, value)` / store the digested failing-test signature on the
  job row. **Add column** `jobs.failing_signature TEXT` (recreated in `init_db`).
- Daily-spend window via existing `meta`:
  - `get_daily_spend(today_str) -> float` — read `meta` key `daily_spend:<YYYY-MM-DD>`.
  - `add_daily_spend(today_str, delta)` — upsert `meta.val_real += delta`.
  - `is_loop_paused() -> bool` / `set_loop_paused(bool, reason)` — `meta` key `loop_paused`.

**Gate:** `python -c "import orchestrator.db"` recreates tables cleanly; unit-call each
helper against a temp DB.

---

## Feature 2 — `orchestrator/runner_plugins/reforma_offline_guard.py`

A pytest plugin living **outside the worktree** (agent cannot edit it). It is loaded by
the verify command via `-p reforma_offline_guard`. Two jobs: **block non-loopback
sockets** and **record the collected node-id set** to a runner-controlled file.

### 2.1 Directory & path wiring
1. `mkdir orchestrator/runner_plugins/` and add `__init__.py` (empty).
2. The verify env must prepend this dir to `PYTHONPATH` so `-p reforma_offline_guard`
   resolves (it is NOT inside the worktree). This is done in §6 / `run_tests_background`.

### 2.2 Socket blocking
```python
import socket as _socket

_real_connect = _socket.socket.connect

def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else None
    if host not in ("127.0.0.1", "::1", "localhost", None):
        raise RuntimeError(f"REFORMA offline guard: blocked non-loopback connect to {host}")
    return _real_connect(self, address)
```
- In `pytest_configure(config)`: monkeypatch `socket.socket.connect` (and
  `create_connection`) to `_guarded_connect`. Allow loopback only.
- Guard activates only when `os.environ.get("REFORMA_OFFLINE") == "1"` so local
  developer pytest runs are unaffected.

### 2.3 Node-id recording
- Implement `pytest_collection_modifyitems(session, config, items)`:
  collect `sorted({item.nodeid for item in items})`.
- Write the set as JSON to the path in env var `REFORMA_NODEID_OUT` (a
  runner-controlled file under `C:\rf\session\<task-id>\nodeids.json`, **outside** the
  worktree). If the env var is missing, no-op (so the plugin is safe in dev).
- Write happens at collection time so it fires even if tests then fail.

### 2.4 Marker registration
- `pytest_configure` also registers the `online` marker
  (`config.addinivalue_line("markers", "online: requires network/browser/Gemini")`)
  to avoid unknown-marker warnings, since `pyproject.toml`/`pytest.ini` is agent-denied.

**Gate:** running the §4 command with the plugin: a test that does
`socket.create_connection(("8.8.8.8", 53))` errors; `nodeids.json` is written with the
collected set; `-m "not online"` excludes `@pytest.mark.online` tests.

---

## Feature 3 — Circuit breakers

Implemented in two layers: **live session breakers** (inside `session_runner.py`,
acting during the stream) and **driver-level breakers** (inside `driver.py`, acting
between attempts using DB state). Monotonic clock (`time.monotonic()`); timestamps
stored as epoch in `meta`/`changesets` to survive hibernate.

### 3.1 Live session breakers (`session_runner.py`)
Modify the stream-parse loop in `launch_session()`:

| Guard | Threshold | Mechanism |
|---|---|---|
| Cost / session | `$5` hard kill | track running `total_cost_usd`; when exceeded, `proc.kill()` + close job handle, return `stop_reason="cost_kill"`. |
| Wall clock / session | 15 min **active agent time** | accumulate monotonic time **excluding** intervals where the agent is awaiting a `run_tests`/`get_test_result` tool result (detect by tool-call markers in stream-json); on exceed, kill + `stop_reason="walltime_kill"`. |
| Max turns | 30 (50 if task tagged `large`) | pass `--max-turns` (already present); also count `turn_start` as a backstop. Driver passes the limit based on a `large` tag column. |

- `launch_session` returns an extended dict: `{success, exit_code, cost, turns, text,
  stderr, stop_reason}` where `stop_reason ∈ {completed, cost_kill, walltime_kill,
  max_turns, error}`.
- Kill path must close `h_job` (job-object kill-on-close already guarantees child-tree
  termination) and persist `cost` to the ledger via `db.add_ledger_entry`.

### 3.2 Driver-level breakers (`driver.py`, evaluated per attempt)
Centralize in a `check_breakers(task) -> BreakerDecision` helper returning one of
`CONTINUE | ESCALATE | FAIL | PAUSE_LOOP`, with a reason string for `attempts.md`.

| Guard | Threshold | Source | On trip |
|---|---|---|---|
| Consecutive failed attempts / task | 3 | `tasks.attempts_count` + last-N job results | `ESCALATED` + attempts.md note |
| Identical-diff | `git patch-id --stable` repeats 2× | `db.count_patch_id(task, patch_id)` | `ESCALATED` |
| Oscillation | same `(patch_id, failing-test signature)` recurs | `db.get_recent_attempt_signatures` | `ESCALATED` |
| Cost / task | `$10` | `tasks.spend_usd` vs `tasks.budget_usd` | `ESCALATED` |
| Daily global | `$75` (alert at 80%) | `db.get_daily_spend(today)` | `set_loop_paused(True)` |
| Global breaker | ≥5 task failures / hour | count `tasks` moved to FAILED in last 3600s (epoch in `meta` ring or query `updated_at`) | pause loop + enqueue canary verify at last-known-good to classify env-vs-agent |

- **patch-id --stable:** update the patch-id computation in `submit_changeset`
  (currently `git patch-id`) to `git patch-id --stable` for determinism; store in
  `changesets.patch_id`. The breaker reads counts from there.
- **Oscillation signature:** define `failing-test signature = sorted failing node-ids +
  first traceback frame`, digested by the gate/driver from the job `result_payload`
  (reuse the digest helper from §5.3). Stored on `jobs.failing_signature`.
- **Canary:** a driver routine `run_canary()` that runs the §4 verify at the repo's
  last-known-good commit in a throwaway worktree; green ⇒ classify recent failures as
  *agent*, red ⇒ *environment* (log + keep loop paused).

**Gate:** unit tests that seed DB rows trip each breaker deterministically (CLAUDE.md
Phase-2 gate: "breakers trip on a stuck task").

---

## Feature 5 — Test-weakening (reward-hacking) gate

Server-side, not bypassable by the agent. Runs **after** each green verify, before a
task may move `TESTING → QUEUED`. Lives in a new module
`orchestrator/test_gate.py`, called from `run_tests_background` (§6).

### 5.1 Baseline capture
- On first verify for a `base_commit` (or in driver intake), run a **collection-only**
  pass (`pytest --co -q -p reforma_offline_guard`) at the clean base worktree with
  `REFORMA_NODEID_OUT` set, then `db.record_node_baseline(base_commit, node_ids)`.

### 5.2 Per-attempt comparison
After a passing run, read the attempt's `nodeids.json` (written by the plugin, §2.3):
- **Shrink check:** if `set(attempt) ⊂ set(baseline)` (any baseline node-id missing) ⇒
  `flagged_for_review`, CANNOT auto-count as success.
- **Protected-path check:** if the changeset touched any of
  `tests/**`, `conftest.py`, `pytest.ini`, or `pyproject.toml [tool.pytest]` ⇒
  `flagged_for_review`. (Derive touched paths from the changeset operations recorded
  for the attempt; persist the touched-path list on the changeset or a small
  `attempt_files` table.)
- A green run that passes both checks ⇒ eligible for `QUEUED`.
- A flagged run ⇒ task → `ESCALATED` (human review), with reason in `attempts.md`.

### 5.3 Output digest helper
`digest_pytest_output(raw: str) -> dict` returning
`{passed: bool, failing_node_ids: [...], first_frames: [...], tail: "..."}` —
shared by the gate, the oscillation breaker (§3.2), and `attempts.md` (§4). This is the
server-side digest CLAUDE.md §4 requires (`get_logs` still serves full logs by ref).

**Gate (CLAUDE.md Phase-3):** an attempt that deletes/weakens a `tests/` file, or whose
collected set shrank, is flagged and cannot auto-succeed.

---

## Feature 4 — `attempts.md` generation

Harness-written, ~4 KB, last 4 attempts. `write_attempts_journal()` already exists in
`session_runner.py`; this feature adds the **generator** that builds the markdown the
driver feeds to fresh sessions. Put it in `orchestrator/attempts.py`.

### 4.1 Generator
`build_attempts_journal(task_id) -> str`:
1. Pull last 4 attempts via `db.get_recent_attempt_signatures(task_id, 4)`.
2. For each attempt render:
   - attempt number,
   - changeset `patch-id` (stable),
   - changed files (from §5.2 touched-path list),
   - failing-test signature (node-ids + first traceback frame, from §5.3 digest),
   - one-line hypothesis (the agent's stated hypothesis captured from the prior
     session text, or `"(none recorded)"`).
3. Hard-cap to ~4 KB (truncate oldest first), keep newest 4.

### 4.2 Wiring
- The **driver** calls `build_attempts_journal(task_id)` before launching a *fresh*
  session and passes the string to `launch_session(..., attempts_journal=...)`, which
  already writes it to `C:\rf\session\<id>\attempts.md` and appends it to the brief.
- **Resume vs fresh policy** (CLAUDE.md §2.6): within a single fix cycle use
  `--resume`; start fresh across attempts or past ~150k context tokens. The driver
  decides and only generates/passes `attempts.md` on fresh starts. (`session_runner`
  needs a `--resume <session_id>` path added; capture the CLI session id from the
  stream-json `init`/`system` message and persist it on the task.)

**Gate:** after a failed attempt, `attempts.md` exists, is ≤~4 KB, lists the prior
attempt's patch-id + failing signature; a fresh session's brief contains it.

---

## Feature 1 — `orchestrator/driver.py` (state machine & loop)

The driver is the orchestration brain, run as a background task in the dev-loop process
(§6). It owns the state machine transitions that are **not** triggered by agent tool
calls. It never touches the primary working tree; all `.git` mutations go through
`git_manager.git_lock`.

### 1.1 Structure
```python
class Driver:
    def __init__(self, repo_path, bearer_token, poll_interval=5.0): ...
    def run_forever(self):        # main loop, daemon thread
    def tick(self):               # one pass over actionable tasks
    def _intake_pending(self):    # PENDING → ASSIGNED (worktree + session)
    def _drain_queued(self):      # QUEUED → rebase_and_verify → READY/ESCALATE/ASSIGNED
    def _apply_breakers(self, task): # §3.2
```

### 1.2 Intake: `PENDING → ASSIGNED`
Per CLAUDE.md §2.3:
1. Under `git_lock`: `create_worktree(repo, task_id, base_commit)`.
2. Write `.mcp.json` (bearer) via `session_runner.write_mcp_config`.
3. `build_attempts_journal(task_id)` (empty on first attempt).
4. `launch_session(...)` (blocking per task; driver may run one session at a time, or a
   small bounded pool — cap concurrent test jobs at 1/worktree, ~2 global per §2.7).
5. On session return, branch on `stop_reason`:
   - the agent itself calls `submit_changeset` + `run_tests` during the session, which
     drives `ASSIGNED → TESTING → QUEUED|FAILED` via the MCP tools;
   - `cost_kill`/`walltime_kill`/`max_turns`/`error` ⇒ count as failed attempt, run
     `_apply_breakers`, decide retry-vs-escalate by `stop_reason`.

### 1.3 Drain: `QUEUED → …`
For each `QUEUED` task (CLAUDE.md §2.4), call
`git_manager.rebase_and_verify(repo, task_id, verify_func)` where `verify_func` runs the
§4 command **with the offline guard + node-id capture + test-weakening gate** (reuse the
same code path as `run_tests_background`, factored into a shared `verify_worktree()`):
- `READY_FOR_REVIEW` ⇒ `update_task_status_cas(task, "REBASING"→"READY_FOR_REVIEW")`.
  **The loop stops here.** No `git checkout`/`merge` in the primary tree.
- `CONFLICT` ⇒ `ESCALATED`.
- `VERIFY_FAILED` ⇒ back to `ASSIGNED`, `increment_task_attempts`, then breakers.
- Set `REBASING` while in flight so crash recovery can reset it.

### 1.4 State transitions owned by the driver
```
PENDING ──intake──▶ ASSIGNED            (driver)
ASSIGNED ─ via MCP submit_changeset/run_tests ─▶ TESTING ─▶ QUEUED | (red)→ASSIGNED
QUEUED  ──rebase clean + verify green──▶ READY_FOR_REVIEW   (driver; LOOP STOPS)
QUEUED  ──conflict──▶ ESCALATED                              (driver)
QUEUED  ──verify red──▶ ASSIGNED (attempts++)                (driver)
any ──breaker──▶ ESCALATED ; unrecoverable ──▶ FAILED        (driver)
```

### 1.5 Idempotency & concurrency
- All status moves use `update_task_status_cas` (already present) to avoid races with
  the MCP tools.
- Respect disk-space floor before `create_worktree` (CLAUDE.md §2.7); janitor sweep of
  orphan worktrees/logs runs each tick or on a timer.
- The driver holds **no** new lock; it shares `git_manager.git_lock` for `.git` ops.

**Gate (CLAUDE.md Phase-2):** end-to-end `PENDING → READY_FOR_REVIEW` with a real fix;
breakers trip on a stuck task; duplicate submit is idempotent; restart recovers cleanly.

---

## Feature 6 — Integrate the driver into `mcp_server.py`

### 6.1 Launch the driver as a startup background task
Extend the existing `@app.on_event("startup")`:
```python
@app.on_event("startup")
async def startup_event():
    init_session_token()
    orchestrator_db.init_db()
    run_crash_recovery()                 # extend: also reset REBASING → QUEUED, prune orphan worktrees
    global _driver
    _driver = Driver(repo_path=REPO_ROOT, bearer_token=BEARER_TOKEN)
    t = threading.Thread(target=_driver.run_forever, daemon=True)
    t.start()
```
- The driver runs in the **same process** as the MCP tools (single in-process git lock,
  per CLAUDE.md §2.1). It imports nothing from the cookie/Playwright app.
- Add a clean-shutdown hook (`@app.on_event("shutdown")`) to signal the driver to stop.

### 6.2 Rewire `run_tests_background` to the pinned §4 command + plugin + gate
Replace the current command:
```python
cmd = [python_exe, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not online", "tests/"]
```
with the pinned spec:
```python
cmd = [python_exe, "-m", "pytest", "-q",
       "-p", "no:cacheprovider",
       "-p", "reforma_offline_guard",
       "-m", "not online", "tests/"]
```
And the env (extend the existing strip block):
```python
env["REFORMA_OFFLINE"] = "1"
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["PYTHONIOENCODING"] = "utf-8"
env["REFORMA_NODEID_OUT"] = str(SESSION_BASE_DIR / task_id / "nodeids.json")
runner_plugins = str(BASE_DIR / "runner_plugins")
env["PYTHONPATH"] = runner_plugins + os.pathsep + env.get("PYTHONPATH", "")
# keys_to_remove already strips GEMINI/ANTHROPIC/etc.; ensure bearer token never in env
```
After `proc.communicate`:
1. `digest = test_gate.digest_pytest_output(output)` (§5.3) → store
   `jobs.failing_signature` + `result_payload`.
2. If green: run `test_gate.check_weakening(task_id, base_commit, nodeids_path, touched_files)`:
   - clean ⇒ `TESTING → QUEUED` (current behavior),
   - flagged ⇒ `TESTING → ESCALATED` (do **not** auto-succeed).
3. If red: `TESTING → FAILED`? — **change** current behavior: red verify should return
   the task to `ASSIGNED` (attempt++) so the driver/breakers can retry, per the state
   machine. Move the FAIL/ESCALATE decision to the driver's `_apply_breakers`.

### 6.3 Factor a shared `verify_worktree(worktree_path, task_id, base_commit) -> dict`
Both `run_tests_background` (agent-triggered) and `rebase_and_verify`'s `verify_func`
(driver-triggered, §1.3) call this single helper so the offline guard, node-id capture,
and the weakening gate are identical on both paths. Avoids drift between the agent's
test run and the post-rebase verify.

### 6.4 Extend crash recovery (§2.7)
In `run_crash_recovery`:
- reap `RUNNING` jobs → `FAILED` (exists),
- reset `TESTING` → `ASSIGNED` (exists),
- **add:** reset `REBASING` → `QUEUED`,
- **add:** prune orphan worktrees (`git worktree prune` + sweep `C:\rf\wt\*` with no DB
  task),
- **add:** clear stale `loop_paused` only if the operator set an auto-resume flag;
  otherwise keep paused.

**Gate:** start `mcp_server.py`; a hand-fed `PENDING` task flows to `READY_FOR_REVIEW`
without manual intervention; killing the process mid-`TESTING`/`REBASING` and
restarting recovers to a consistent state.

---

## Cross-cutting: minimal `tests/` additions to exercise the new code

CLAUDE.md §4 expects `tests/test_triage.py` + `tests/fixtures/`. To make the gates
testable, add (these are repo tests, NOT agent-edited):
- `tests/fixtures/` — valid + malformed `rooms_turboflow.json` / `turboflow_ready.csv`.
- `tests/test_triage.py` — golden tests for `triage.verify_turboflow_outputs`.
- `tests/test_offline_guard.py` — asserts non-loopback connect is blocked and
  `nodeids.json` is written (run with the plugin).
- `tests/test_breakers.py` — seed DB, assert each breaker decision.
- `tests/test_gate.py` — shrunk node-id set and `tests/**` touch are both flagged.

---

## Sequencing summary

1. **DB helpers + `node_id_baselines` table** (§0) — unblocks gate/breakers/driver.
2. **`reforma_offline_guard.py`** (§2) — needed by every verify run.
3. **`test_gate.py`** (§5) incl. `digest_pytest_output` — shared by breakers + attempts.
4. **Breakers** (§3) — live (session_runner) + driver-level.
5. **`attempts.py`** (§4) — consumes digest + signatures.
6. **`driver.py`** (§1) — ties intake/drain/breakers together.
7. **mcp_server integration** (§6) — launch driver, rewire verify to pinned command +
   plugin + gate, extend crash recovery.

Each step ends green/red deterministically against the §4 command before moving on,
matching the CLAUDE.md Phase-2 and Phase-3 gates.
