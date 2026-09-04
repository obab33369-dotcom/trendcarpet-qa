import os
import sys
import uuid
import json
import time
import secrets
import logging
import asyncio
import threading
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Inject path for local imports
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import db as orchestrator_db
import git_manager as orchestrator_git
import changeset as orchestrator_changeset
from driver import Driver, verify_worktree

# Setup Logging
logger = logging.getLogger("orchestrator.mcp")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "mcp_server.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Auth Token Setup
TOKEN_PATH = Path(r"C:\rf\session\token")
BEARER_TOKEN = None

def init_session_token() -> str:
    global BEARER_TOKEN
    try:
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        BEARER_TOKEN = secrets.token_hex(32)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(BEARER_TOKEN)
        os.chmod(TOKEN_PATH, 0o600)
        logger.info(f"Initialized secure local session token in {TOKEN_PATH}")
        return BEARER_TOKEN
    except Exception as e:
        logger.critical(f"Failed to initialize session token: {e}")
        sys.exit(1)

# Initialize FastAPI and FastMCP
app = FastAPI(title="REFORMA Developer Loop MCP App")
mcp = FastMCP("REFORMA Developer Loop MCP")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Verify Authorization header on all SSE and tool endpoints served under /mcp
    if request.url.path.startswith("/mcp"):
        auth_header = request.headers.get("Authorization")
        if not BEARER_TOKEN:
            return JSONResponse(status_code=500, content={"detail": "Bearer token not initialized."})
        if not auth_header or auth_header != f"Bearer {BEARER_TOKEN}":
            return JSONResponse(status_code=401, content={"detail": "Unauthorized. Invalid or missing bearer token."})
    return await call_next(request)

# Crash Recovery Routine
def run_crash_recovery():
    logger.info("Executing orchestrator startup crash recovery...")
    conn = orchestrator_db.get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Find all active/running jobs and mark them FAILED
        cursor.execute("UPDATE jobs SET status = 'FAILED', completed_at = ? WHERE status = 'RUNNING'", (datetime.now().isoformat(),))
        reaped_jobs = cursor.rowcount
        if reaped_jobs > 0:
            logger.info(f"Reaped {reaped_jobs} running test jobs.")
            
        # 2. Reset tasks stuck in TESTING or ASSIGNED status back to PENDING
        cursor.execute("UPDATE tasks SET status = 'PENDING', updated_at = ? WHERE status IN ('TESTING', 'ASSIGNED')", (datetime.now().isoformat(),))
        reaped_tasks = cursor.rowcount
        if reaped_tasks > 0:
            logger.info(f"Reset {reaped_tasks} tasks back to PENDING state.")
            
        # 3. Reset tasks stuck in REBASING status back to QUEUED
        cursor.execute("UPDATE tasks SET status = 'QUEUED', updated_at = ? WHERE status = 'REBASING'", (datetime.now().isoformat(),))
        reaped_rebases = cursor.rowcount
        if reaped_rebases > 0:
            logger.info(f"Reset {reaped_rebases} tasks back to QUEUED state.")
            
        conn.commit()
    except Exception as e:
        logger.error(f"Error during crash recovery: {e}")
    finally:
        conn.close()
        
    # Prune orphan worktrees on startup
    try:
        repo_path = BASE_DIR.parent
        subprocess.run(["git", "worktree", "prune"], cwd=str(repo_path), capture_output=True)
    except Exception as e:
        logger.warning(f"Failed to run git worktree prune: {e}")

_driver = None

@app.on_event("startup")
async def startup_event():
    init_session_token()
    orchestrator_db.init_db()
    run_crash_recovery()
    
    global _driver
    _driver = Driver(repo_path=BASE_DIR.parent, bearer_token=BEARER_TOKEN)
    t = threading.Thread(target=_driver.run_forever, daemon=True)
    t.start()

@app.on_event("shutdown")
async def shutdown_event():
    global _driver
    if _driver:
        logger.info("Stopping REFORMA Developer Loop Driver...")
        _driver.stop()

# ----------------- MCP TOOLS -----------------

@mcp.tool()
def get_logs(service: str, level: str = "INFO", limit: int = 100) -> str:
    """
    Retrieves the latest logs for the specified service.
    Supported services: 'mcp_server', 'triage'.
    """
    log_file = None
    if service == "mcp_server":
        log_file = BASE_DIR / "mcp_server.log"
    elif service == "triage":
        log_file = BASE_DIR / "triage.log"
    else:
        return f"Unknown service: {service}. Supported: 'mcp_server', 'triage'."
        
    if not log_file or not log_file.exists():
        return f"No logs found for service {service}."
        
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        filtered = [l for l in lines if level.upper() in l] if level else lines
        tail = filtered[-limit:]
        return "".join(tail)
    except Exception as e:
        return f"Error reading logs: {e}"

@mcp.tool()
def list_locks() -> str:
    """
    Lists all active resource locks (leases) and their details.
    """
    conn = orchestrator_db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leases")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "No active locks."
    
    res = []
    for r in rows:
        res.append(f"Resource: {r['resource_path']} | Owner Task: {r['owner_task_id']} | PID: {r['owner_pid']} | Expires: {r['expires_at']}")
    return "\n".join(res)

@mcp.tool()
def get_triage_metrics() -> str:
    """
    Returns live metrics including spend, failure rates, queue depth, and retry counts.
    """
    conn = orchestrator_db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status, count(*) as count FROM tasks GROUP BY status")
    task_stats = {r['status']: r['count'] for r in cursor.fetchall()}
    
    cursor.execute("SELECT sum(cost_usd) as total_spend FROM ledger")
    spend_row = cursor.fetchone()
    total_spend = spend_row['total_spend'] if spend_row and spend_row['total_spend'] else 0.0
    
    conn.close()
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "total_spend_usd": total_spend,
        "task_counts_by_status": task_stats
    }
    return json.dumps(metrics, indent=2)

def run_tests_background(task_id: str, job_id: str, worktree_path: Path):
    """
    Background worker running offline pytest suite inside Windows Job Object.
    """
    logger.info(f"Background thread: Spawning tests for task {task_id}, job {job_id}")
    
    task = orchestrator_db.get_task(task_id)
    target_branch = orchestrator_git.get_target_branch(BASE_DIR.parent)
    base_commit = task.get("base_commit", target_branch)
    
    # Run the verification suite using the shared driver verify function
    res = verify_worktree(worktree_path, task_id, base_commit)
    
    status = "COMPLETED" if res["success"] else "FAILED"
    output = res["output"]
    
    try:
        conn = orchestrator_db.get_db_connection()
        cursor = conn.cursor()
        now = datetime.isoformat(datetime.now())
        
        # Get digested failing signature
        failing_sig = ",".join(res["digest"]["failing_node_ids"]) if res["digest"]["failing_node_ids"] else ""
        
        cursor.execute("""
            UPDATE jobs
            SET status = ?, result_payload = ?, failing_signature = ?, completed_at = ?
            WHERE job_id = ?
        """, (status, output, failing_sig, now, job_id))
        
        # TESTING -> QUEUED if verification passes; FAILED or Weakened -> PENDING for retry
        task_status = "QUEUED" if status == "COMPLETED" else "PENDING"
        
        cursor.execute("""
            UPDATE tasks
            SET status = ?, updated_at = ?
            WHERE task_id = ? AND status = 'TESTING'
        """, (task_status, now, task_id))
        
        conn.commit()
        conn.close()
    except Exception as ex:
        logger.error(f"Failed to update database for task {task_id}, job {job_id}: {ex}")
        
    logger.info(f"Background thread: Finished tests for task {task_id}, job {job_id}. Status: {status}")

@mcp.tool()
async def run_tests(task_id: str) -> str:
    """
    Triggers an asynchronous test execution run in the task's worktree.
    Returns a unique job_id immediately.
    """
    def _db_work():
        task = orchestrator_db.get_task(task_id)
        if not task:
            return None, {"error": f"Task {task_id} not found."}
            
        worktree_path = orchestrator_git.WORKTREE_BASE_DIR / task_id
        if not worktree_path.exists():
            return None, {"error": f"Worktree for task {task_id} does not exist."}
            
        job_id = str(uuid.uuid4())
        now = datetime.isoformat(datetime.now())
        
        conn = orchestrator_db.get_db_connection()
        cursor = conn.cursor()
        
        # Prevent concurrent test runs for the same task
        cursor.execute("SELECT 1 FROM jobs WHERE task_id = ? AND status = 'RUNNING'", (task_id,))
        if cursor.fetchone():
            conn.close()
            return None, {"error": f"A test job is already running for task {task_id}."}
            
        cursor.execute("""
            INSERT INTO jobs (job_id, task_id, job_type, status, started_at)
            VALUES (?, ?, 'TEST', 'RUNNING', ?)
        """, (job_id, task_id, now))
        
        # Compare-and-set transition from ASSIGNED to TESTING
        cursor.execute("""
            UPDATE tasks
            SET status = 'TESTING', updated_at = ?
            WHERE task_id = ? AND status = 'ASSIGNED'
        """, (now, task_id))
        
        conn.commit()
        conn.close()
        return job_id, worktree_path

    res = await asyncio.to_thread(_db_work)
    if isinstance(res, tuple) and res[0] is None:
        return json.dumps(res[1])
        
    job_id, worktree_path = res
    t = threading.Thread(target=run_tests_background, args=(task_id, job_id, worktree_path))
    t.daemon = True
    t.start()
    
    return json.dumps({"job_id": job_id, "status": "RUNNING"})

def _fetch_job_row(job_id: str):
    conn = orchestrator_db.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

@mcp.tool()
async def get_test_result(job_id: str, wait_seconds: int = 120) -> str:
    """
    Retrieves the status and output of a test job. Supports long-polling.
    """
    start_time = time.time()
    while True:
        row = await asyncio.to_thread(_fetch_job_row, job_id)
        if not row:
            return json.dumps({"error": f"Job {job_id} not found."})
            
        status = row["status"]
        if status != "RUNNING" or (time.time() - start_time) >= wait_seconds:
            return json.dumps({
                "job_id": job_id,
                "status": status,
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "result_payload": row["result_payload"]
            })
            
        await asyncio.sleep(1.0)

@mcp.tool()
async def submit_changeset(task_id: str, changeset_payload: str) -> str:
    """
    Validates and writes changes directly to the existing worktree.
    Enforces idempotency and tracks patch signatures.
    """
    try:
        changeset = json.loads(changeset_payload)
    except Exception as e:
        return json.dumps({"error": f"Invalid JSON payload: {e}"})
        
    # Check for duplicate submission using payload hash
    payload_bytes = json.dumps(changeset, sort_keys=True).encode("utf-8")
    changeset_id = hashlib.sha256(payload_bytes).hexdigest()
    
    # 1. Idempotency Check
    existing_cs = await asyncio.to_thread(orchestrator_db.get_changeset, changeset_id)
    if existing_cs:
        logger.info(f"Changeset {changeset_id} has already been applied. Skipping duplicate write.")
        worktree_path = orchestrator_git.WORKTREE_BASE_DIR / task_id
        return json.dumps({"status": "APPLIED", "worktree_path": str(worktree_path), "changeset_id": changeset_id})
        
    target_branch = orchestrator_git.get_target_branch(BASE_DIR.parent)
    base_commit = changeset.get("base_commit", target_branch)
    worktree_path = orchestrator_git.WORKTREE_BASE_DIR / task_id
    
    if not worktree_path.exists():
        return json.dumps({"error": f"Worktree directory for task {task_id} does not exist."})
        
    def _apply_work():
        # Validate and apply changeset directly on the existing worktree
        success = orchestrator_changeset.apply_changeset(worktree_path, changeset)
        if success:
            # Compute a stable patch-id to detect duplicates/oscillations
            patch_id = "unknown"
            try:
                # Add all files (including new/untracked files) to Git tracking to stable-hash new tests
                subprocess.run(["git", "add", "-A"], cwd=str(worktree_path), check=True)
                # Get the git patch-id of the changes
                diff_proc = subprocess.run(["git", "diff", "--cached"], cwd=str(worktree_path), capture_output=True, check=True)
                patch_proc = subprocess.run(["git", "patch-id", "--stable"], input=diff_proc.stdout, capture_output=True, check=True)
                patch_id = patch_proc.stdout.decode("utf-8").strip().split(" ")[0]
            except Exception as e:
                logger.warning(f"Failed to generate git patch-id: {e}")
                
            # Log the changeset and patch signature to DB
            orchestrator_db.add_changeset(changeset_id, task_id, patch_id)
            
            # Move state to ASSIGNED so it is ready for run_tests
            orchestrator_db.update_task_status_cas(task_id, "PENDING", "ASSIGNED")
            orchestrator_db.update_task_status_cas(task_id, "TESTING", "ASSIGNED")
        return success
        
    try:
        success = await asyncio.to_thread(_apply_work)
    except ValueError as val_err:
        return json.dumps({"error": str(val_err)})
    except Exception as e:
        return json.dumps({"error": f"Failed to apply changeset: {e}"})
        
    if not success:
        return json.dumps({"error": "Failed to apply changeset to worktree. Concurrency conflict or NTFS validation error."})
        
    return json.dumps({"status": "APPLIED", "worktree_path": str(worktree_path), "changeset_id": changeset_id})

# Mount the MCP SSE application onto FastAPI under "/mcp"
app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    # Bind only to localhost for security
    uvicorn.run(app, host="127.0.0.1", port=8765)
