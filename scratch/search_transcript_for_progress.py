import json
import os

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    print("Transcript not found.")
else:
    print("Reading transcript...")
    user_msgs = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                step = json.loads(line)
                if step.get("type") == "USER_INPUT":
                    content = step.get("content", "")
                    user_msgs.append(content)
            except Exception:
                pass
                
    print(f"Total user messages: {len(user_msgs)}")
    print("\nLast 15 user messages:")
    for i, msg in enumerate(user_msgs[-15:]):
        print(f"[{i+1}] {msg}")
