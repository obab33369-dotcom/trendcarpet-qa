import os
import json
import shutil

def main():
    # Paths
    src_img = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2\AGJM5060.JPG"
    dest_img = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup\AGJM5060.JPG"
    output_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    
    # Copy file to backup folder
    if os.path.exists(src_img):
        shutil.copy2(src_img, dest_img)
        print("Copied AGJM5060.JPG to Backup folder.")
    else:
        print("Source AGJM5060.JPG not found!")
        return
        
    # Update JSON mapping
    if os.path.exists(output_json):
        with open(output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        data["AGJM5060.JPG"] = {
            "number": "535",
            "digits_read": ["5", "3", "5"],
            "confidence": "high"
        }
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Updated cowhide_numbers.json with AGJM5060 -> 535.")

if __name__ == "__main__":
    main()
