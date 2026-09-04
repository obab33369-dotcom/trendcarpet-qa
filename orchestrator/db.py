import sqlite3
import os
import time
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "orchestrator.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tasks Table (with updated CHECK constraint)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT NOT NULL CHECK(status IN ('PENDING', 'ASSIGNED', 'TESTING', 'QUEUED', 'REBASING', 'READY_FOR_REVIEW', 'MERGED', 'FAILED', 'ESCALATED')),
            base_commit TEXT NOT NULL,
            branch_name TEXT NOT NULL,
            budget_usd REAL NOT NULL,
            spend_usd REAL DEFAULT 0.0,
            attempts_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # 2. Jobs Table (for async testing runs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            job_type TEXT NOT NULL CHECK(job_type IN ('TEST', 'MERGE')),
            status TEXT NOT NULL CHECK(status IN ('RUNNING', 'COMPLETED', 'FAILED')),
            result_payload TEXT,
            failing_signature TEXT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
    """)
    
    # 3. Leases Table (lock management with PID + Start Time)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leases (
            resource_path TEXT PRIMARY KEY,
            owner_task_id TEXT NOT NULL,
            owner_pid INTEGER NOT NULL,
            owner_start_time TEXT NOT NULL,
            expires_at REAL NOT NULL, -- Epoch float timestamp
            FOREIGN KEY (owner_task_id) REFERENCES tasks (task_id)
        )
    """)
    
    # 4. Ledger Table (cost tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            tokens_in INTEGER NOT NULL,
            tokens_out INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
    """)

    # 5. Changesets Table (idempotency + patch-id breakers)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS changesets (
            changeset_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            patch_id TEXT NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
    """)

    # 6. Meta Table (locks andSpend tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            val_text TEXT,
            val_real REAL
        )
    """)
    
    # 7. Node ID Baselines Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS node_id_baselines (
            base_commit TEXT PRIMARY KEY,
            node_ids TEXT NOT NULL,   -- JSON array of node-id strings
            created_at REAL NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# Helper operations for Tasks
def create_task(task_id: str, base_commit: str, branch_name: str, budget_usd: float = 10.0) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.isoformat(datetime.now())
    try:
        cursor.execute("""
            INSERT INTO tasks (task_id, status, base_commit, branch_name, budget_usd, spend_usd, attempts_count, created_at, updated_at)
            VALUES (?, 'PENDING', ?, ?, ?, 0.0, 0, ?, ?)
        """, (task_id, base_commit, branch_name, budget_usd, now, now))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Task already exists
    
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_task_status(task_id: str, new_status: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.isoformat(datetime.now())
    cursor.execute("""
        UPDATE tasks 
        SET status = ?, updated_at = ?
        WHERE task_id = ?
    """, (new_status, now, task_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def update_task_status_cas(task_id: str, old_status: str, new_status: str) -> bool:
    """
    Compare-and-set task status update to ensure thread safety.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.isoformat(datetime.now())
    cursor.execute("""
        UPDATE tasks 
        SET status = ?, updated_at = ?
        WHERE task_id = ? AND status = ?
    """, (new_status, now, task_id, old_status))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def increment_task_attempts(task_id: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tasks 
        SET attempts_count = attempts_count + 1, updated_at = ?
        WHERE task_id = ?
    """, (datetime.isoformat(datetime.now()), task_id))
    conn.commit()
    cursor.execute("SELECT attempts_count FROM tasks WHERE task_id = ?", (task_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def add_ledger_entry(task_id: str, session_id: str, tokens_in: int, tokens_out: int, cost_usd: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.isoformat(datetime.now())
    
    cursor.execute("""
        INSERT INTO ledger (task_id, session_id, tokens_in, tokens_out, cost_usd, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (task_id, session_id, tokens_in, tokens_out, cost_usd, now))
    
    cursor.execute("""
        UPDATE tasks 
        SET spend_usd = spend_usd + ?, updated_at = ?
        WHERE task_id = ?
    """, (cost_usd, now, task_id))
    
    conn.commit()
    conn.close()

def get_task(task_id: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

# Changesets Helpers
def add_changeset(changeset_id: str, task_id: str, patch_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    try:
        cursor.execute("""
            INSERT INTO changesets (changeset_id, task_id, patch_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (changeset_id, task_id, patch_id, now))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def get_changeset(changeset_id: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM changesets WHERE changeset_id = ?", (changeset_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def get_changesets_for_task(task_id: str) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM changesets WHERE task_id = ? ORDER BY created_at ASC", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Meta Helpers
def get_meta(key: str, default_text: str = None, default_real: float = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT val_text, val_real FROM meta WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["val_text"], row["val_real"]
    return default_text, default_real

def set_meta(key: str, val_text: str = None, val_real: float = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meta (key, val_text, val_real)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET val_text = excluded.val_text, val_real = excluded.val_real
    """, (key, val_text, val_real))
    conn.commit()
    conn.close()

# New helper functions for Antigravity 2.0
import json

def record_node_baseline(base_commit: str, node_ids: list) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    node_ids_json = json.dumps(node_ids)
    cursor.execute("""
        INSERT OR REPLACE INTO node_id_baselines (base_commit, node_ids, created_at)
        VALUES (?, ?, ?)
    """, (base_commit, node_ids_json, now))
    conn.commit()
    conn.close()

def get_node_baseline(base_commit: str) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT node_ids FROM node_id_baselines WHERE base_commit = ?", (base_commit,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["node_ids"])
    return None

def count_patch_id(task_id: str, patch_id: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM changesets WHERE task_id = ? AND patch_id = ?", (task_id, patch_id))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_recent_attempt_signatures(task_id: str, n: int = 4) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.patch_id, j.failing_signature, j.result_payload
        FROM changesets c
        LEFT JOIN jobs j ON c.task_id = j.task_id
        WHERE c.task_id = ?
        ORDER BY c.created_at DESC
        LIMIT ?
    """, (task_id, n))
    rows = cursor.fetchall()
    conn.close()
    
    signatures = []
    for r in rows:
        signatures.append({
            "patch_id": r["patch_id"],
            "failing_signature": r["failing_signature"],
            "result_payload": r["result_payload"]
        })
    return signatures

def update_job_failing_signature(job_id: str, failing_signature: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs
        SET failing_signature = ?
        WHERE job_id = ?
    """, (failing_signature, job_id))
    conn.commit()
    conn.close()

def get_daily_spend(today_str: str) -> float:
    key = f"daily_spend:{today_str}"
    _, val = get_meta(key, default_real=0.0)
    return val

def add_daily_spend(today_str: str, delta: float):
    key = f"daily_spend:{today_str}"
    _, current = get_meta(key, default_real=0.0)
    set_meta(key, val_real=current + delta)

def is_loop_paused() -> bool:
    val, _ = get_meta("loop_paused", default_text="false")
    return val.lower() == "true"

def set_loop_paused(paused: bool, reason: str = None):
    val_text = "true" if paused else "false"
    set_meta("loop_paused", val_text=val_text)
    if reason:
        set_meta("loop_paused_reason", val_text=reason)

# Initialize DB on import
init_db()
