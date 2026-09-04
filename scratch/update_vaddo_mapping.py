import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
SKU_MAP_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
BRAND_DICT_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

def main():
    # 1. Update brand_sku_dict.json
    if os.path.exists(BRAND_DICT_PATH):
        with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
            brand_dict = json.load(f)
            
        # Add Barstol Väddö Beige
        brand_dict["barstol-vaddo-beige"] = {
            "sku": "102612",
            "name": "Barstol 'Väddö' - Beige",
            "url": "https://www.reformasthlm.se/sv/barstol-vaddo-beige",
            "image_path": "/bilder/artiklar/102612.jpg"
        }
        
        with open(BRAND_DICT_PATH, 'w', encoding='utf-8') as f:
            json.dump(brand_dict, f, indent=2, ensure_ascii=False)
        print("Updated brand_sku_dict.json successfully!")
    else:
        print("brand_sku_dict.json not found!")

    # 2. Update sku_map.json
    if os.path.exists(SKU_MAP_PATH):
        with open(SKU_MAP_PATH, 'r', encoding='utf-8') as f:
            sku_map = json.load(f)
            
        # Locate the key for 1558
        target_key = None
        for k in sku_map.keys():
            if k.startswith("1558_"):
                target_key = k
                break
                
        if target_key:
            print(f"Found target key in sku_map.json: '{target_key}'")
            print(f"Old value: {sku_map[target_key]}")
            sku_map[target_key] = {
                "sku": "102612",
                "slug": "barstol-vaddo-beige",
                "url": "https://www.reformasthlm.se/sv/barstol-vaddo-beige",
                "current_images": ["/bilder/artiklar/102612.jpg"]
            }
            print(f"New value: {sku_map[target_key]}")
            
            with open(SKU_MAP_PATH, 'w', encoding='utf-8') as f:
                json.dump(sku_map, f, indent=2, ensure_ascii=False)
            print("Updated sku_map.json successfully!")
        else:
            print("No key starting with '1558_' found in sku_map.json!")
    else:
        print("sku_map.json not found!")

if __name__ == "__main__":
    main()
