import os
import json

log_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\36bef6e6-a57c-4707-8fd1-2b263d4f0e8f\.system_generated\logs\transcript.jsonl"
print("Scanning:", log_file)

if os.path.exists(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("type") == "USER_INPUT":
                        content = data.get("content", "").strip()
                        print(f"[{data.get('step_index')}] {content}")
                        print("-" * 50)
                except Exception as e:
                    pass
    except Exception as e:
        print("Error:", e)
else:
    print("Does not exist.")
