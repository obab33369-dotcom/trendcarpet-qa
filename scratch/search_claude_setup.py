import os
import json

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\.system_generated\logs\transcript.jsonl"

if os.path.exists(transcript_path):
    print(f"Reading transcript: {transcript_path}")
    count = 0
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                content = str(data.get("content", ""))
                if any(x in content.lower() for x in ["claude", "anthropic", "key", "cli", "integration"]):
                    print(f"\n--- STEP {data.get('step_index')} (Type: {data.get('type')}) ---")
                    print(content[:1000] + ("..." if len(content) > 1000 else ""))
                    count += 1
                    if count >= 15:
                        print("\nReached max print limit of 15 matches.")
                        break
            except Exception:
                pass
    print(f"\nTotal matching steps: {count}")
else:
    print(f"Transcript not found at: {transcript_path}")
