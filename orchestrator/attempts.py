import os
import re
import json
from pathlib import Path

ATTEMPTS_BASE_DIR = Path(r"C:\rf\session")

def extract_hypothesis(session_text: str) -> str:
    if not session_text:
        return ""
    # Match Hypothesis: <text> or hypothesis: <text>
    match = re.search(r"(?:hypothesis|Hypothesis):\s*(.*)", session_text)
    if match:
        return match.group(1).strip()
    return ""

def log_attempt(task_id: str, attempt_num: int, patch_id: str, changed_files: list, failing_signature: str, hypothesis: str):
    session_dir = ATTEMPTS_BASE_DIR / task_id
    session_dir.mkdir(parents=True, exist_ok=True)
    history_path = session_dir / "history.json"
    
    history = []
    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass
            
    # Add new attempt
    history.append({
        "number": attempt_num,
        "patch_id": patch_id,
        "changed_files": changed_files,
        "failing_signature": failing_signature,
        "hypothesis": hypothesis
    })
    
    # Keep only last 4 attempts
    history = history[-4:]
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def build_attempts_journal(task_id: str) -> str:
    session_dir = ATTEMPTS_BASE_DIR / task_id
    history_path = session_dir / "history.json"
    
    if not history_path.exists():
        return ""
        
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return ""
        
    lines = []
    for att in history:
        lines.append(f"### Attempt #{att['number']}")
        lines.append(f"- **Patch ID (stable):** `{att['patch_id']}`")
        
        files_str = ", ".join(att['changed_files']) if att['changed_files'] else "(none)"
        lines.append(f"- **Changed files:** {files_str}")
        
        sig = att['failing_signature'] or "Passed all tests"
        lines.append(f"- **Failing test signature:** {sig}")
        
        hyp = att['hypothesis'] or "(none recorded)"
        lines.append(f"- **Hypothesis:** {hyp}")
        lines.append("")
        
    journal = "\n".join(lines)
    
    # Truncate to ~4 KB if needed
    if len(journal.encode("utf-8")) > 4000:
        while len(journal.encode("utf-8")) > 4000 and len(history) > 1:
            history.pop(0)
            lines = []
            for att in history:
                lines.append(f"### Attempt #{att['number']}")
                lines.append(f"- **Patch ID (stable):** `{att['patch_id']}`")
                files_str = ", ".join(att['changed_files']) if att['changed_files'] else "(none)"
                lines.append(f"- **Changed files:** {files_str}")
                sig = att['failing_signature'] or "Passed all tests"
                lines.append(f"- **Failing test signature:** {sig}")
                hyp = att['hypothesis'] or "(none recorded)"
                lines.append(f"- **Hypothesis:** {hyp}")
                lines.append("")
            journal = "\n".join(lines)
            
    return journal
