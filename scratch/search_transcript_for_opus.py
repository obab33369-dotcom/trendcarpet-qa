import os
import json

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    # Try parent directory or list directories to find it
    print(f"Transcript not found at: {transcript_path}")
    base_dir = os.path.dirname(os.path.dirname(transcript_path))
    if os.path.exists(base_dir):
        print(f"Listing items under {base_dir}:")
        print(os.listdir(base_dir))
else:
    print(f"Reading transcript: {transcript_path}")
    count = 0
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                content = str(data.get("content", ""))
                # Search for mentions of "opus" in user input or assistant response
                if "opus" in content.lower():
                    print(f"\n--- STEP {data.get('step_index')} (Type: {data.get('type')}) ---")
                    # print truncated content
                    print(content[:1000] + ("..." if len(content) > 1000 else ""))
                    count += 1
            except Exception as e:
                pass
    print(f"\nTotal steps matching 'opus': {count}")
