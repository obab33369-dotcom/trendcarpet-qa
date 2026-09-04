import os
import json
import shutil
from PIL import Image

def main():
    base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides"
    orig_backup_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    verification_dir = os.path.join(base_dir, "Batch 2 - Rotated Verification")
    final_json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_final.json"
    
    with open(final_json_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    print("Clearing verification directory...")
    if os.path.exists(verification_dir):
        for item in os.listdir(verification_dir):
            item_path = os.path.join(verification_dir, item)
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                except Exception:
                    pass
    else:
        os.makedirs(verification_dir, exist_ok=True)
        
    print("Regenerating verification photos...")
    count = 0
    for filename, info in db.items():
        base = os.path.splitext(filename)[0]
        number = info.get("number")
        
        orig_path = os.path.join(orig_backup_dir, filename)
        if not os.path.exists(orig_path):
            orig_path = os.path.join(orig_backup_dir, f"{base}.JPG")
            if not os.path.exists(orig_path):
                orig_path = os.path.join(orig_backup_dir, f"{base}.png")
                
        if os.path.exists(orig_path):
            dest_file = os.path.join(verification_dir, f"{number}-{base}.jpg")
            img = Image.open(orig_path)
            img.convert('RGB').save(dest_file, format="JPEG", quality=85)
            count += 1
        else:
            print(f"Original not found for {base}")
            
    print(f"Completed! Generated {count} verification photos.")

if __name__ == "__main__":
    main()
