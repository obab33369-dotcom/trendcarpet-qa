import os
import json

brain_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain"
print("All directories in brain:")
try:
    for d in os.listdir(brain_dir):
        path = os.path.join(brain_dir, d)
        if os.path.isdir(path):
            print(f"  {d}")
            # print first user input of this conversation to know what it is
            log_file = os.path.join(path, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "USER_INPUT":
                                print(f"    First request: {data.get('content')[:120].strip()}")
                                break
                        except Exception:
                            pass
except Exception as e:
    print("Error:", e)
