import json
import os

def main():
    output_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    if not os.path.exists(output_json):
        print("Results file not found")
        return
        
    with open(output_json, 'r', encoding='utf-8') as f:
        results = json.load(f)
        
    suspicious = {}
    for filename, data in results.items():
        if "error" in data:
            suspicious[filename] = f"ERROR: {data['error']}"
            continue
        num = str(data.get("number", ""))
        if len(num) != 3:
            suspicious[filename] = num
            
    print("=== SUSPICIOUS OR NON-3DIGIT RESULTS ===")
    for filename, val in sorted(suspicious.items()):
        print(f"{filename} -> {val}")
        
if __name__ == "__main__":
    main()
