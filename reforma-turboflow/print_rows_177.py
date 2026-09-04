import json

json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for idx in range(175, 180):
    row = data[idx]
    print(f"--- ROW #{idx+1} ---")
    print(f"Prompt: {row['prompt']}")
    print(f"References: {row['image_references']}")
    print(f"Tags: {row['image_tags']}")
