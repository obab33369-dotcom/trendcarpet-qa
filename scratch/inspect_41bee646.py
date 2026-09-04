import os
import json

log_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\.system_generated\logs\transcript.jsonl"
print("Scanning:", log_file)

if os.path.exists(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("type") == "USER_INPUT":
                        idx = data.get('step_index')
                        content = data.get("content", "").strip()
                        print(f"[{idx}] {content}")
                        print("-" * 50)
                except Exception as e:
                    pass
    except Exception as e:
        print("Error:", e)
else:
    print("Does not exist.")
