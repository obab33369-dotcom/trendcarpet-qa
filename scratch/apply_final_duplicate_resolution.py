import os
import json
import shutil
import glob

def main():
    base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides"
    orig_backup_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    processed_1500_dir = os.path.join(base_dir, "Batch 2 - Processed (1500x1500)")
    processed_orig_dir = os.path.join(base_dir, "Batch 2 - Processed (Original Size)")
    combined_dir = os.path.join(base_dir, "Batch 2 - Combined Folders")
    verification_dir = os.path.join(base_dir, "Batch 2 - Rotated Verification")
    final_json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_final.json"
    
    # 1. Load database
    with open(final_json_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    # Apply change
    db["OTYL1698.JPG"]["number"] = "523"
    with open(final_json_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print("Updated database: OTYL1698.JPG -> 523")
    
    # 2. Rename in Processed Folders
    def rename_processed(directory):
        files = [f for f in os.listdir(directory) if f.lower().endswith('.jpg')]
        for f in files:
            parts = f.split('-')
            if len(parts) >= 2 and parts[1].upper() == "OTYL1698":
                new_name = f"523-OTYL1698-{"-".join(parts[2:])}"
                os.rename(os.path.join(directory, f), os.path.join(directory, new_name))
                print(f"Renamed file in {os.path.basename(directory)}: {f} -> {new_name}")
                
    rename_processed(processed_1500_dir)
    rename_processed(processed_orig_dir)
    
    # 3. Rename in Combined Folders
    old_sub = os.path.join(combined_dir, "352-OTYL1698")
    new_sub = os.path.join(combined_dir, "523-OTYL1698")
    if os.path.exists(old_sub):
        if os.path.exists(new_sub):
            shutil.rmtree(new_sub)
        os.rename(old_sub, new_sub)
        print(f"Renamed folder in Combined Folders: 352-OTYL1698 -> 523-OTYL1698")
        
        # Rename files inside the folder
        for f in os.listdir(new_sub):
            f_path = os.path.join(new_sub, f)
            if os.path.isfile(f_path):
                if f.startswith("352-"):
                    new_f = f.replace("352-", "523-", 1)
                    os.rename(f_path, os.path.join(new_sub, new_f))
                    
    # 4. Update in Verification
    old_ver = os.path.join(verification_dir, "352-OTYL1698.jpg")
    new_ver = os.path.join(verification_dir, "523-OTYL1698.jpg")
    if os.path.exists(old_ver):
        if os.path.exists(new_ver):
            os.remove(new_ver)
        os.rename(old_ver, new_ver)
        print("Renamed verification image: 352-OTYL1698.jpg -> 523-OTYL1698.jpg")

if __name__ == "__main__":
    main()
