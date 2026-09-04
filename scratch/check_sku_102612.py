import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
SKU_MAP_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
BRAND_DICT_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

def check_sku(filepath, sku):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n--- Checking for '{sku}' in {os.path.basename(filepath)} ---")
    found = False
    for k, v in data.items():
        if sku in str(k) or sku in json.dumps(v):
            print(f"Match: {k} -> {v}")
            found = True
    if not found:
        print("Not found.")

def main():
    check_sku(SKU_MAP_PATH, "102612")
    check_sku(BRAND_DICT_PATH, "102612")

if __name__ == "__main__":
    main()
