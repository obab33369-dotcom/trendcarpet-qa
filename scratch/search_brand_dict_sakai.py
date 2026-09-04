import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
BRAND_DICT_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

def main():
    if not os.path.exists(BRAND_DICT_PATH):
        print("brand_sku_dict.json not found.")
        return
        
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("=== SEARCHING BRAND DICT FOR SAKAI ===")
    found = False
    for k, v in data.items():
        if "sakai" in k.lower() or "sakai" in json.dumps(v).lower():
            print(f"Key: {k} -> {v}")
            found = True
            
    if not found:
        print("Sakai not found in brand_sku_dict.json.")

if __name__ == "__main__":
    main()
