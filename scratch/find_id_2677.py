import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_for_value(filename, value):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        return
        
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for idx, item in enumerate(data):
        item_str = json.dumps(item)
        if str(value) in item_str:
            print(f"Found {value} in {filename} at index {idx}:")
            print(json.dumps(item, indent=2))
            return True
    return False

def main():
    print("Searching for 2677...")
    search_for_value("rooms_turboflow_full_catalog.json", 2677)
    search_for_value("rooms_turboflow_batch2.json", 2677)
    search_for_value("rooms_turboflow_batch1.json", 2677)
    
    print("\nSearching for 1941...")
    search_for_value("rooms_turboflow_full_catalog.json", 1941)
    search_for_value("rooms_turboflow_batch2.json", 1941)
    search_for_value("rooms_turboflow_batch1.json", 1941)

if __name__ == "__main__":
    main()
