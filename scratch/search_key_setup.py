import os
import json
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\.system_generated\logs\transcript_full.jsonl"
if not os.path.exists(transcript_path):
    transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\.system_generated\logs\transcript.jsonl"

out_file = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\claude_setup_log.txt"

if os.path.exists(transcript_path):
    matches = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                content = str(data.get("content", ""))
                if any(x in content.lower() for x in ["claude", "anthropic", "key", "cli", "integration"]):
                    matches.append((data.get("step_index"), data.get("type"), content))
            except Exception:
                pass
                
    print(f"Total matching steps: {len(matches)}. Writing to {out_file}")
    with open(out_file, 'w', encoding='utf-8') as out:
        for step, step_type, content in matches:
            out.write(f"\n=================== STEP {step} ({step_type}) ===================\n")
            out.write(content)
            out.write("\n")
else:
    print("Transcript not found")
