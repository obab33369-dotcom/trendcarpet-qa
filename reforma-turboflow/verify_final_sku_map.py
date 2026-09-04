import json
import os

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"
SKU_MAP_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\sku_map.json"

def should_skip_item(filename: str) -> bool:
    fname = filename.lower()
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    
    def c_str(s):
        repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
        for c, r in repl.items(): s = s.replace(c, r)
        return s.lower()
        
    cleaned_fname = c_str(fname)
    for kw in skip_keywords:
        if kw in fname or c_str(kw) in cleaned_fname:
            return True
    return False

def main():
    if not os.path.exists(DB_PATH):
        print(f"[FAIL] Error: DB not found at {DB_PATH}")
        return
    if not os.path.exists(SKU_MAP_PATH):
        print(f"[FAIL] Error: SKU map not found at {SKU_MAP_PATH}")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    with open(SKU_MAP_PATH, "r", encoding="utf-8") as f:
        sku_map = json.load(f)
        
    active_keys = sorted([k for k in db.keys() if not should_skip_item(k)])
    
    mapped_count = 0
    unmapped_keys = []
    
    for key in active_keys:
        if key in sku_map and sku_map[key].get("sku"):
            mapped_count += 1
        else:
            unmapped_keys.append(key)
            
    print("==================================================")
    print("           FINAL SKU MAP PIPELINE COVERAGE        ")
    print("==================================================")
    print(f"[OK] Total active items in Batch 2 DB: {len(active_keys)}")
    print(f"[OK] Total items successfully mapped: {mapped_count}")
    print(f"[OK] Coverage rate: {(mapped_count / len(active_keys)) * 100:.2f}%")
    print("==================================================")
    
    if unmapped_keys:
        print(f"⚠️ Unmapped items ({len(unmapped_keys)}):")
        for k in unmapped_keys[:10]:
            print(f"  - {k}")
        if len(unmapped_keys) > 10:
            print(f"  ... and {len(unmapped_keys) - 10} more.")
    else:
        print("[SUCCESS] 100% Perfect Coverage! All active items mapped successfully!")
    print("==================================================")

if __name__ == "__main__":
    main()
