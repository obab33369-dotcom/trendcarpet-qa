import json
import os

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs\transcript.jsonl"
print("Transcript exists:", os.path.exists(transcript_path))

if os.path.exists(transcript_path):
    user_inputs = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    user_inputs.append(data)
            except Exception as e:
                print("Error parsing line:", e)
                
    print(f"Found {len(user_inputs)} user inputs:")
    for idx, inp in enumerate(user_inputs):
        content = inp.get("content", "")
        # print first 150 chars
        print(f"[{idx+1}] {content[:200]}...")
