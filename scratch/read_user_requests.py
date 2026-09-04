import json
import os

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\9a89adb6-c2a2-4ca2-a186-3ca3c4d5681e\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    print("Transcript not found:", transcript_path)
    exit(1)

user_messages = []
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('type') == 'USER_INPUT':
                user_messages.append((data.get('step_index'), data.get('content')))
        except Exception as e:
            pass

print(f"Total user messages found: {len(user_messages)}")
for step, content in user_messages[-10:]:
    print(f"\n--- STEP {step} ---")
    print(content)
