import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
SKU_MAP_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')

def main():
    if not os.path.exists(SKU_MAP_PATH):
        print("sku_map.json not found.")
        return
        
    with open(SKU_MAP_PATH, 'r', encoding='utf-8') as f:
        sku_map = json.load(f)
        
    # Find the Sakai key
    target_key = None
    for k in sku_map.keys():
        if "3638_" in k:
            target_key = k
            break
            
    if target_key:
        print(f"Found Sakai key: {target_key}")
        print(f"Old value: {sku_map[target_key]}")
        sku_map[target_key] = {
            "sku": "9965",
            "slug": "byra-sakai",
            "url": "https://www.reformasthlm.se/sv/byra-sakai",
            "current_images": ["/bilder/artiklar/9965.jpg"]
        }
        print(f"New value: {sku_map[target_key]}")
        
        with open(SKU_MAP_PATH, 'w', encoding='utf-8') as f:
            json.dump(sku_map, f, indent=2, ensure_ascii=False)
        print("Updated sku_map.json successfully!")
    else:
        print("Sakai key not found in sku_map.json!")

if __name__ == "__main__":
    main()
