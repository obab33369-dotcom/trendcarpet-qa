import os

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\36bef6e6-a57c-4707-8fd1-2b263d4f0e8f\.system_generated\logs\transcript.jsonl"
output_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\interior-designer-automation\transcript_matches.txt"

matches = []
if os.path.exists(transcript_path):
    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            # Look for outputs of previous runs or elements
            if "Printing all active elements" in line or "El " in line or "datorval" in line or "dator" in line:
                # Store the line number and the line content (truncated if too long)
                matches.append(f"Line {idx}: {line[:300]}")

with open(output_path, "w", encoding="utf-8") as out:
    out.write(f"Found {len(matches)} matches in transcript.jsonl:\n\n")
    for m in matches[-50:]:  # Let's write the last 50 matches
        out.write(m + "\n")

print(f"Done, saved {len(matches)} matches to {output_path}")
