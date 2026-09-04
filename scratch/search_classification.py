import os
import json

JSON_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\empty_folders_classification.json"

def main():
    if not os.path.exists(JSON_PATH):
        print("JSON file not found.")
        return
        
    print("Searching classification JSON...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    found = False
    for k, v in data.items():
        if "matgrupp28" in k or "matgrupp28" in str(v):
            print(f"Key: {k}")
            print(json.dumps(v, indent=2)[:500])
            print("-" * 50)
            found = True
            
    if not found:
        print("No occurrences of 'matgrupp28' found.")

if __name__ == "__main__":
    main()
