import os
import json

DB_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_full_catalog.json"

def main():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Database type: {type(data)}")
    print(f"Length of data: {len(data)}")
    
    # Print the first 3 items in detail
    for i, item in enumerate(data[:3]):
        print(f"\nItem [{i}]:")
        for k, v in item.items():
            print(f"  {k}: {type(v)} = {str(v)[:150]}...")

if __name__ == "__main__":
    main()
