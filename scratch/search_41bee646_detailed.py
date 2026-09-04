import os
import json
import re

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
                        # check if it contains dates like YYYY-MM-DD or DD-MM-YY or folder names with dates
                        # e.g. 26-06-05 or similar, or lists of numbers
                        if any(kw in content.lower() for kw in ["batch", "datum", "nummer", "senaste", "körn", "antal"]):
                            print(f"[{idx}] {content[:300]}")
                            print("-" * 50)
                except Exception as e:
                    pass
    except Exception as e:
        print("Error:", e)
else:
    print("Does not exist.")
