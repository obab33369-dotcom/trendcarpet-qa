import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root and orchestrator to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "orchestrator"))

import db as orchestrator_db

def seed():
    task_id = "test-task-e2e"
    base_commit = "945f4f4"  # latest master commit
    branch_name = "reforma/task/test-task-e2e"
    
    # 1. Clean up old E2E task from DB
    conn = orchestrator_db.get_db_connection()
    conn.execute("DELETE FROM ledger WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM leases WHERE owner_task_id = ?", (task_id,))
    conn.execute("DELETE FROM jobs WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM changesets WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    # 2. Write brief.txt
    brief_dir = Path(r"C:\rf\session") / task_id
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief_path = brief_dir / "brief.txt"
    
    brief_content = (
        "Hello! Please add a dummy Python comment at the end of orchestrator/config.py "
        "stating '# E2E verification comment'. Do not modify or add any files in the tests/ directory. "
        "Once done, the tests will pass automatically."
    )
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief_content)
    print(f"Wrote brief.txt to {brief_path}")
    
    # 3. Create task in PENDING state
    task = orchestrator_db.create_task(task_id, base_commit, branch_name)
    print(f"Created task in DB: {task}")

if __name__ == "__main__":
    seed()
