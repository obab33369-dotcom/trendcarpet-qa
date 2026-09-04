import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
SKU_MAP_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
BRAND_DICT_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

def search_json(filepath, term):
    term = term.lower()
    matches = []
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return matches
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if isinstance(data, dict):
        for k, v in data.items():
            k_str = str(k).lower()
            v_str = json.dumps(v, ensure_ascii=False).lower()
            if term in k_str or term in v_str:
                matches.append((k, v))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            item_str = json.dumps(item, ensure_ascii=False).lower()
            if term in item_str:
                matches.append((idx, item))
    return matches

def main():
    terms = ["vadd", "vaddo", "väddö", "vestby"]
    
    for term in terms:
        print(f"\n================ SEARCHING FOR '{term}' ================")
        
        sku_map_matches = search_json(SKU_MAP_PATH, term)
        print(f"sku_map.json matches ({len(sku_map_matches)}):")
        for k, v in sku_map_matches:
            print(f"  Key: {k} -> {v}")
            
        brand_matches = search_json(BRAND_DICT_PATH, term)
        print(f"brand_sku_dict.json matches ({len(brand_matches)}):")
        for k, v in brand_matches[:10]:
            print(f"  Key: {k} -> {v}")

if __name__ == "__main__":
    main()
