import json
import os

paths = [
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\sku_composition_overrides.json",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\sku_composition_overrides.json"
]

for p in paths:
    if os.path.exists(p):
        print(f"Updating overrides in: {p}")
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        sku_override = data.setdefault("1400042", {})
        slot_override = sku_override.setdefault("1", {
            "adjust_x": 0,
            "adjust_y": 0,
            "scale_factor_override": None,
            "tolerance": 5.0,
            "blend_range": 30.0
        })
        
        slot_override["highlight_threshold"] = 170.0
        slot_override["highlight_factor"] = 0.4
        
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Updated successfully.")
    else:
        print(f"Path does not exist: {p}")
