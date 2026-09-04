import json
import os

cache_paths = [
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\classification_cache.json",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\classification_cache.json"
]

new_entries = {
    # Slot 1
    "type_1400042_1_135959_1780065812": "studio",
    "has_white_bg_1400042_1_135959_1780065812": True,
    "zoom_1400042_1_135959_1780065812": False,
    
    # Slot 2
    "type_1400042_2_515644_1780065812": "detail",
    "has_white_bg_1400042_2_515644_1780065812": True,
    "zoom_1400042_2_515644_1780065812": True,
    
    # Slot 3
    "type_1400042_3_614691_1780065813": "detail",
    "has_white_bg_1400042_3_614691_1780065813": True,
    "zoom_1400042_3_614691_1780065813": True,
    
    # Slot 4
    "type_1400042_4_890531_1780065813": "detail",
    "has_white_bg_1400042_4_890531_1780065813": True,
    "zoom_1400042_4_890531_1780065813": True,
    
    # Slot 5
    "type_1400042_5_103260_1780065813": "detail",
    "has_white_bg_1400042_5_103260_1780065813": True,
    "zoom_1400042_5_103260_1780065813": True
}

for path in cache_paths:
    if os.path.exists(path):
        print(f"Updating cache at: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        # Add new entries
        for k, v in new_entries.items():
            cache[k] = v
            
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
        print("Success.")
    else:
        print(f"Path does not exist: {path}")
