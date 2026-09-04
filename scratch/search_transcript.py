import json
import os

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    print("Transcript not found at", transcript_path)
    exit(1)

keywords = ["margin", "touch", "lamp", "table", "studio", "bypassed", "zoom", "edge"]

with open(transcript_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            content = data.get("content", "")
            if not content:
                continue
            matches = [kw for kw in keywords if kw.lower() in content.lower()]
            if matches:
                # Print step index, source, and a snippet of content matching
                print(f"Step {data.get('step_index')} ({data.get('source')}): matches {matches}")
                # Print lines containing the matches
                for l in content.split("\n"):
                    if any(kw.lower() in l.lower() for kw in keywords):
                        print("  ", l[:120])
        except Exception as e:
            pass
