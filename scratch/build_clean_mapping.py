import os
import json

def main():
    standard_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    rotated_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_rotated.json"
    
    with open(standard_json, 'r', encoding='utf-8') as f:
        std_db = json.load(f)
        
    with open(rotated_path := rotated_json, 'r', encoding='utf-8') as f:
        rot_db = json.load(f)
        
    # The inspected problem files and their verified correct values:
    inspected_corrections = {
        "BPQA5442.JPG": "669",
        "OTYL1698.JPG": "352",
        "RXSA5233.JPG": "27",
        "OBSY6632.JPG": "832",
        "AGJM5060.JPG": "355",
        "WYGV2057.JPG": "625",
        "NSPM3714.JPG": "352",
        "HCHH1324.JPG": "258",
        "DGJR8081.JPG": "258",
        "KWHA5687.JPG": "259",
        "YLBS5372.JPG": "259"
    }
    
    # We will build a unified, cleaned mapping.
    # We default to the rotated scan database (which has phone rotation),
    # but overwrite with manual corrections.
    clean_db = {}
    
    # Fill from standard first
    for f, d in std_db.items():
        if "error" not in d:
            clean_db[f] = d.get("number")
            
    # Update from rotated DB (which is generally more accurate due to phone rotation)
    for f, d in rot_db.items():
        if "error" not in d:
            num = d.get("number")
            # For rotated DB, handle duplicate digits or bad readings
            if num and len(num) == 3: # Keep 3 digit ones
                clean_db[f] = num
            elif num == "013" or num == "063": # Valid 3 digit with leading zero
                clean_db[f] = num
                
    # Apply corrections
    for f, num in inspected_corrections.items():
        clean_db[f] = num
        
    # Let's print out the unified mapping and check for duplicates or gaps
    counts = {}
    for f, num in clean_db.items():
        counts[num] = counts.get(num, []) + [f]
        
    print("=== CLEANED MAPPING FREQUENCIES ===")
    for num in sorted(counts.keys()):
        files = counts[num]
        print(f"Number {num}: {files}")
        
    # Save to a new verified file
    verified_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_verified.json"
    with open(verified_json, 'w', encoding='utf-8') as f:
        json.dump(clean_db, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(clean_db)} files mapping to {verified_json}")

if __name__ == "__main__":
    main()
