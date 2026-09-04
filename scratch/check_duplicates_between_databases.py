import json
import os

def main():
    json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    rotated_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_rotated.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    with open(rotated_path, 'r', encoding='utf-8') as f:
        db_rot = json.load(f)
        
    # Analyze db (standard)
    counts = {}
    for filename, data in db.items():
        num = data.get("number")
        counts[num] = counts.get(num, []) + [filename]
        
    print("=== Duplicates in standard cowhide_numbers.json ===")
    for num, files in sorted(counts.items()):
        if len(files) > 1:
            print(f"Number {num}: {files}")
            for f in files:
                rot_data = db_rot.get(f, {})
                rot_num = rot_data.get("number", "N/A")
                print(f"  - rotated DB says: {f} -> {rot_num} (rotation: {rot_data.get('rotation_angle', 0)}°)")
                
    # Check mismatches between the two
    mismatches = []
    for filename, data in db.items():
        if filename in db_rot:
            num = data.get("number")
            rot_num = db_rot[filename].get("number")
            if num != rot_num:
                mismatches.append((filename, num, rot_num, db_rot[filename].get("rotation_angle", 0)))
                
    print("\n=== Mismatches between standard and rotated DB ===")
    for filename, old_num, new_num, angle in sorted(mismatches):
        print(f"{filename}: standard={old_num} | rotated={new_num} (rotation={angle}°)")

if __name__ == "__main__":
    main()
