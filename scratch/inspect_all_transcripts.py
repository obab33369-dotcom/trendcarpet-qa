import os
import json

brain_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain"
print("Scanning brain directory:", brain_dir)

if os.path.exists(brain_dir):
    try:
        subdirs = os.listdir(brain_dir)
        print(f"Found {len(subdirs)} conversation directories.")
        for d in subdirs:
            # check if it looks like a uuid
            if len(d) == 36 and d.count('-') == 4:
                log_file = os.path.join(brain_dir, d, ".system_generated", "logs", "transcript.jsonl")
                if os.path.exists(log_file):
                    print(f"\nScanning transcript for conversation: {d}")
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines_count = 0
                            for line in f:
                                try:
                                    data = json.loads(line)
                                    if data.get("type") == "USER_INPUT":
                                        content = data.get("content", "")
                                        # Look for dates like 2026-06 or formats like 26-06 or batch numbers
                                        if any(kw in content.lower() for kw in ["datum", "batch", "nummer", "senaste"]):
                                            print(f"  Match in {d}: {content.strip()}")
                                except Exception:
                                    pass
                    except Exception as e_read:
                        print(f"  Error reading {d}: {e_read}")
    except Exception as e:
        print("Error listing brain dir:", e)
else:
    print("Brain directory does not exist.")
