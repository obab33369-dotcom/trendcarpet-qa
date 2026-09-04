import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
SKU_MAP_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
BRAND_DICT_PATH = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

def search_terms(filepath, terms):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n=== Searching {os.path.basename(filepath)} ===")
    for term in terms:
        print(f"--- Term: {term} ---")
        matches = 0
        for k, v in data.items():
            k_str = str(k).lower()
            v_str = json.dumps(v, ensure_ascii=False).lower()
            if term.lower() in k_str or term.lower() in v_str:
                matches += 1
                print(f"  {k} -> {v}")
                if matches >= 15:
                    print("  ... showing first 15 matches")
                    break
        if matches == 0:
            print("  No matches found.")

def main():
    terms = ["ystad", "pinnstol", "elsa", "montmartre", "elegant", "astrid"]
    search_terms(BRAND_DICT_PATH, terms)

if __name__ == "__main__":
    main()
