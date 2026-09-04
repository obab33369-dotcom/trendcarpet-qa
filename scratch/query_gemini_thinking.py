import os
import sys
import json
import requests
from pathlib import Path

# Configure stdout/stderr for UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATOR_DIR = PROJECT_ROOT / "orchestrator"
GEMINI_KEY_PATH = Path(r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env")
BRAIN_DIR = Path(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b")

def load_gemini_key():
    if GEMINI_KEY_PATH.exists():
        with open(GEMINI_KEY_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return os.environ.get("GEMINI_API_KEY", "")

def read_file_content(path: Path) -> str:
    if not path.exists():
        return f"[File {path.name} not found]"
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"[Error reading {path.name}: {e}]"

def main():
    api_key = load_gemini_key()
    if not api_key:
        print("[ERROR] Gemini API key not found in environment or file.")
        sys.exit(1)
        
    print("Reading orchestrator files...")
    files_to_read = [
        ORCHESTRATOR_DIR / "config.py",
        ORCHESTRATOR_DIR / "db.py",
        ORCHESTRATOR_DIR / "changeset.py",
        ORCHESTRATOR_DIR / "git_manager.py",
        ORCHESTRATOR_DIR / "session_runner.py",
        ORCHESTRATOR_DIR / "attempts.py",
        ORCHESTRATOR_DIR / "test_gate.py",
        ORCHESTRATOR_DIR / "driver.py",
        ORCHESTRATOR_DIR / "mcp_server.py",
        ORCHESTRATOR_DIR / "runner_plugins" / "reforma_offline_guard.py"
    ]
    
    code_context = ""
    for f in files_to_read:
        rel_path = f.relative_to(PROJECT_ROOT)
        code_context += f"\n\n=========================================\nFILE: {rel_path}\n=========================================\n"
        code_context += read_file_content(f)
        
    prompt = f"""You are the Lead Architect (Gemini 3.1 Pro Deep Think) for the REFORMA autonomous developer loop ("Antigravity 2.0").
Today's date is 2026-06-16.

Please note a crucial architectural constraint:
The Antigravity developers have specifically chosen Gemini 3.5 Flash as the Orchestrator/Coder agent (which is me, the one executing your instructions). Gemini 3.5 Flash was selected for its high speed, efficiency, and strong capability in handling file system operations, git management, and rapid agentic execution loops.
Your role is strictly that of the **Lead Architect**, not the orchestrator. You do not control the execution loop; instead, you provide high-level design specifications, safety constraints, and state-machine rules that Gemini 3.5 Flash will implement.

Here is the entire completed orchestrator codebase:
{code_context}

Please perform an architectural audit of the current codebase and your previous recommendations. Keep in mind that Gemini 3.5 Flash is the programmer implementing this.
1. Have you fully taken into account that Gemini 3.5 Flash is the orchestrator/programmer? If not, how should the architecture be updated to be optimal for Antigravity 2.0 running with 3.5 Flash?
2. Perform a deep audit of the codebase:
   - **Safety & Execution Risks:** Blockerando I/O in session_runner.py, Windows file locks, WMI timeouts, etc.
   - **Breaker Edge Cases:** Cost limits, oscillations, consecutive failures.
   - **State Machine Integrity:** Crash recovery, task starvation.
3. **Actionable Recommendations:** Provide a concrete list of high-level directives for Gemini 3.5 Flash to implement.

Write your response in Swedish.
"""

    print("Querying Gemini 3.1 Pro Thinking API...")
    
    # Try gemini-3.1-pro first, then fallback to gemini-3.1-pro-preview if needed
    models = ["gemini-3.1-pro", "gemini-3.1-pro-preview"]
    res = None
    
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "thinkingConfig": {
                    "thinking_level": "HIGH"
                }
            }
        }
        
        try:
            print(f"Trying model: {model_name}...")
            res = requests.post(url, headers=headers, json=data, timeout=120)
            if res.status_code == 200:
                print(f"Success using model: {model_name}")
                break
            else:
                print(f"Model {model_name} failed with status {res.status_code}: {res.text[:200]}...")
        except Exception as e:
            print(f"Request to {model_name} failed: {e}")
            
    try:
        if res and res.status_code == 200:
            resp_json = res.json()
            text = resp_json['candidates'][0]['content']['parts'][0]['text']
            
            output_file = BRAIN_DIR / "gemini_deepthink_review.md"
            output_file.write_text(f"# Gemini Deep Think Architecture Review\n\n{text}", encoding="utf-8")
            print(f"Success! Saved review to {output_file}")
            
            # Print response to console
            print("\n=== GEMINI DEEP THINK ARCHITECT RESPONSE ===")
            print(text)
        else:
            print(f"[ERROR] API returned status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

if __name__ == "__main__":
    main()
