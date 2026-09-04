import json

json_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_batch2.json"
try:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} rows from Batch 2 JSON.")
    for idx in range(212, 220):
        if idx < len(data):
            row = data[idx]
            print(f"\nIndex {idx} (UI #{idx+1}):")
            print(f"  Prompt: {row['prompt']}")
            print(f"  image_references: {row['image_references']}")
            print(f"  image_tags: {row['image_tags']}")
except Exception as e:
    print(f"Error: {e}")
