import os
import json
import re

log_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\.system_generated\logs\transcript.jsonl"
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
                        # Search for ranges like numbers with a dash, e.g. 1530-1580, or batch names
                        match = re.search(r'\d{3,4}-\d{3,4}', content)
                        if match or "batch" in content.lower() or "datum" in content.lower():
                            # Print matching inputs
                            print(f"[{idx}] {content[:300]}")
                            print("-" * 50)
                except Exception as e:
                    pass
    except Exception as e:
        print("Error:", e)
else:
    print("Does not exist.")
