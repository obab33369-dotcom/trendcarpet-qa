import json
import os
import re

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    print("Transcript not found.")
else:
    print("Searching transcript for file counts...")
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                step = json.loads(line)
                content = step.get("content", "")
                
                # Look for numbers of files in model or user messages
                matches = re.findall(r'\b\d{3,5}\b', content)
                if matches and any(word in content.lower() for word in ["bild", "filer", "file", "folder", "mapp", "sorter"]):
                    if step.get("type") in ["USER_INPUT", "PLANNER_RESPONSE"]:
                        print(f"Step {step.get('step_index')} ({step.get('type')}):")
                        print(f"  {content[:300].strip()}...")
                        print("-" * 50)
            except Exception:
                pass
