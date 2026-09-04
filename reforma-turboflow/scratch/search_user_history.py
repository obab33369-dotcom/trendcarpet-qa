import json

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\.system_generated\logs\transcript.jsonl"

try:
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    content = data.get("content", "")
                    if any(w in content.lower() for w in ["avvikelse", "en gång", "undersök", "qa"]):
                        print(f"Step {data.get('step_index')}: {content}")
            except Exception:
                pass
except Exception as e:
    print(f"Error reading transcript: {e}")
