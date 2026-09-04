import os
import json
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

app_data_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity"
brain_dir = os.path.join(app_data_dir, "brain")
out_file = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\fable_transcripts_log.txt"

fable_mentions = []

if os.path.exists(brain_dir):
    for conv_id in os.listdir(brain_dir):
        conv_path = os.path.join(brain_dir, conv_id)
        if not os.path.isdir(conv_path):
            continue
        log_dir = os.path.join(conv_path, ".system_generated", "logs")
        for log_file in ["transcript.jsonl", "transcript_full.jsonl"]:
            p = os.path.join(log_dir, log_file)
            if os.path.exists(p):
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        for line in f:
                            data = json.loads(line)
                            content = str(data.get("content", ""))
                            # Check if the content is a response header or results of Fable 5 run
                            if "fable 5" in content.lower() or "fable-5" in content.lower():
                                if any(x in content.lower() for x in ["response", "result", "error", "cmdlet", "exit"]):
                                    fable_mentions.append((conv_id, data.get("step_index"), data.get("type"), content))
                except Exception:
                    pass

print(f"Total matches: {len(fable_mentions)}. Writing to {out_file}")
with open(out_file, 'w', encoding='utf-8') as out:
    for conv_id, step, step_type, content in fable_mentions:
        out.write(f"\n=================== CONV {conv_id} - STEP {step} ({step_type}) ===================\n")
        out.write(content)
        out.write("\n")
