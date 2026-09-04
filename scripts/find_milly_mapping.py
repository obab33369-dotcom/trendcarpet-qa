import os
import json

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

for file in ["sku_map.json", "furniture_db_batch2.json", "brand_sku_dict.json"]:
    path = os.path.join(project_dir, file)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check if list or dict
        if isinstance(data, dict):
            for k, v in data.items():
                if "3-sitssoffa-milly-be" in str(k) or "3-sitssoffa-milly-be" in str(v):
                    print(f"[{file}] Key: {k} -> Value: {json.dumps(v)[:200]}")
