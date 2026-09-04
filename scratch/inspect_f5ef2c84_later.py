import os
import json

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
                        if 7000 <= idx <= 11800:
                            content = data.get("content", "").strip()
                            # print request if it mentions numbers or dates or batch
                            if any(kw in content.lower() for kw in ["batch", "datum", "nummer", "senaste", "körn", "antal", "bilder", "från", "till"]):
                                print(f"[{idx}] {content[:200]}...")
                                print("-" * 50)
                except Exception as e:
                    pass
    except Exception as e:
        print("Error:", e)
else:
    print("Does not exist.")
