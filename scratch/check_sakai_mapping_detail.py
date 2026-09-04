import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
SKU_MAP_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')

def main():
    if not os.path.exists(SKU_MAP_PATH):
        print("sku_map.json not found.")
        return
        
    with open(SKU_MAP_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("=== CHECKING SAKAI ENTRY ===")
    found = False
    for k, v in data.items():
        if "sakai" in k.lower():
            print(f"Key: {k}")
            print(f"Value: {v}")
            found = True
            
    if not found:
        print("Sakai not found in sku_map.json.")

if __name__ == "__main__":
    main()
