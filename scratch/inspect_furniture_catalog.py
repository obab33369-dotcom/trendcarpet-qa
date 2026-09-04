import os
import json

CATALOG_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\furniture_catalog.json"
CARPET_CATALOG_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\carpet_catalog.json"

def main():
    for name, path in [("Furniture Catalog", CATALOG_PATH), ("Carpet Catalog", CARPET_CATALOG_PATH)]:
        if not os.path.exists(path):
            print(f"{name} not found.")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        print(f"\n{name} keys count: {len(data)}")
        first_keys = list(data.keys())[:3]
        print(f"Sample keys: {first_keys}")
        for k in first_keys:
            print(f"  Key: {k} -> {data[k]}")

if __name__ == "__main__":
    main()
