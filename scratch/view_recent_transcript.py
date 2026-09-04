import json

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs\transcript_full.jsonl"

exchanges = []
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            source = data.get("source")
            step_type = data.get("type")
            content = data.get("content", "")
            if step_type in ("USER_INPUT", "PLANNER_RESPONSE"):
                exchanges.append((source, step_type, content))
        except Exception as e:
            pass

keywords = ["källa", "källor", "source", "borttagna", "ny-sortering", "sortering", "mattor", "möbler"]

matches = []
for idx, (src, stype, content) in enumerate(exchanges):
    content_lower = content.lower()
    if any(kw in content_lower for kw in keywords):
        matches.append((idx, src, stype, content))

print(f"Total keyword matches: {len(matches)}")
# Print the last 15 matching exchanges
for idx, src, stype, content in matches[-15:]:
    print(f"=== Match Index {idx} | Source: {src} | Type: {stype} ===")
    print(content[:500] + ("..." if len(content) > 500 else ""))
