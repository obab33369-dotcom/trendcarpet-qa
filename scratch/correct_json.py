import json
import os

def main():
    path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    if not os.path.exists(path):
        print("File not found")
        return
        
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Update AHIN4169.JPG
    if "AHIN4169.JPG" in data:
        data["AHIN4169.JPG"]["number"] = "633"
        data["AHIN4169.JPG"]["digits_read"] = ["6", "3", "3"]
        data["AHIN4169.JPG"]["confidence"] = "high"
        print("Updated AHIN4169.JPG to 633")
        
    # Update XVVZ1333.JPG
    if "XVVZ1333.JPG" in data:
        data["XVVZ1333.JPG"]["number"] = "433"
        data["XVVZ1333.JPG"]["digits_read"] = ["4", "3", "3"]
        data["XVVZ1333.JPG"]["confidence"] = "high"
        print("Updated XVVZ1333.JPG to 433")
        
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print("Corrections saved.")

if __name__ == "__main__":
    main()
