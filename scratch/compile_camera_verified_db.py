import json
import os

def main():
    standard_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    
    with open(standard_json, 'r', encoding='utf-8') as f:
        std_db = json.load(f)
        
    # We compile the final database based on the camera perspective
    # (reversing the incorrect phone-aligned rotations)
    camera_db = {}
    for filename, d in std_db.items():
        if filename.lower() == "c.jpg":
            continue
        camera_db[filename] = d.get("number")
        
    # Apply the correct values we just verified from the detailed card inspections:
    corrections = {
        "BPQA5442.JPG": "299",
        "OTYL1698.JPG": "352",
        "RXSA5233.JPG": "270",
        "OBSY6632.JPG": "285",
        "AGJM5060.JPG": "535",
        "WYGV2057.JPG": "265",
        "NSPM3714.JPG": "352",
        "ECNJ7018.JPG": "133",
        "CURC8337.JPG": "337",
        "CEYY6720.JPG": "294",
        "WKFI6689.JPG": "319",
        "AHIN4169.JPG": "633",
        "CSKG8106.JPG": "543",
        "FWBU1032.JPG": "723",
        "FZLK0753.JPG": "813",
        "GDQV3716.JPG": "361",
        "HRKU8965.JPG": "643",
        "NNRK8041.JPG": "533",
        "RDIK1368.JPG": "403",
        "TNML9192.JPG": "240",
        "VKTJ0424.JPG": "832"
    }
    
    for filename, num in corrections.items():
        camera_db[filename] = num
        
    # Analyze frequency of each number
    counts = {}
    for filename, num in camera_db.items():
        counts[num] = counts.get(num, []) + [filename]
        
    print("=== FREQUENCIES IN FINAL CAMERA PERSPECTIVE ===")
    duplicates = {}
    for num, files in sorted(counts.items()):
        print(f"Number {num}: {files}")
        if len(files) > 1:
            duplicates[num] = files
            
    print(f"\nTotal files in database: {len(camera_db)}")
    print(f"Duplicates found: {duplicates}")
    
    # Save to verified json
    final_json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_camera_verified.json"
    with open(final_json_path, 'w', encoding='utf-8') as f:
        json.dump(camera_db, f, indent=2, ensure_ascii=False)
    print(f"Saved database to {final_json_path}")

if __name__ == "__main__":
    main()
