import os
import json
import shutil
from PIL import Image

def main():
    # Base paths
    base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides"
    orig_backup_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    
    processed_1500_dir = os.path.join(base_dir, "Batch 2 - Processed (1500x1500)")
    processed_orig_dir = os.path.join(base_dir, "Batch 2 - Processed (Original Size)")
    combined_dir = os.path.join(base_dir, "Batch 2 - Combined Folders")
    verification_dir = os.path.join(base_dir, "Batch 2 - Rotated Verification")
    
    # Load raw mapping database
    standard_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    with open(standard_json, 'r', encoding='utf-8') as f:
        std_db = json.load(f)
        
    # Compile final camera-perspective database
    final_db = {}
    for filename, d in std_db.items():
        if filename.lower() == "c.jpg":
            continue
        final_db[filename] = d.get("number")
        
    # Apply our verified corrections
    corrections = {
        "BPQA5442.JPG": "299",
        "OTYL1698.JPG": "523",
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
        "VKTJ0424.JPG": "832",
        "YLBS5372.JPG": "269"
    }
    
    for filename, num in corrections.items():
        final_db[filename] = num
        
    # Save final JSON
    final_json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_final.json"
    with open(final_json_path, 'w', encoding='utf-8') as f:
        # Save in the same structure as other files for consistency
        json_data = {}
        for filename, num in final_db.items():
            json_data[filename] = {"number": num, "rotation_angle": 0}
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"Saved final camera-perspective database of {len(final_db)} files to {final_json_path}")
    
    # 1. Rename files in processed folders
    print("\nRenaming files in Processed directories...")
    lookup = {k.split('.')[0].lower(): v for k, v in final_db.items()}
    
    def rename_in_directory(directory):
        files = [f for f in os.listdir(directory) if f.lower().endswith('.jpg')]
        for f in files:
            parts = f.split('-')
            if parts[0].isdigit():
                old_num = parts[0]
                base_code = parts[1]
                rest = "-".join(parts[2:])
            else:
                old_num = ""
                base_code = parts[0]
                rest = "-".join(parts[1:])
                
            lookup_key = base_code.lower()
            if lookup_key in lookup:
                correct_num = lookup[lookup_key]
                new_name = f"{correct_num}-{base_code}-{rest}"
                if f != new_name:
                    old_path = os.path.join(directory, f)
                    new_path = os.path.join(directory, new_name)
                    if os.path.exists(new_path):
                        os.remove(old_path)
                    else:
                        os.rename(old_path, new_path)
                        
    rename_in_directory(processed_1500_dir)
    rename_in_directory(processed_orig_dir)
    print("Processed folders updated successfully.")
    
    # 2. Rebuild Combined Folders
    print("\nRebuilding Combined Folders...")
    os.makedirs(combined_dir, exist_ok=True)
    
    # List the existing subfolders in combined_dir
    existing_subs = {}
    for entry in os.listdir(combined_dir):
        entry_path = os.path.join(combined_dir, entry)
        if os.path.isdir(entry_path):
            parts = entry.split('-')
            if len(parts) >= 2:
                code = parts[-1].lower()
                existing_subs[code] = (entry, entry_path)

    # Get the newly renamed list
    renamed_files_1500 = sorted([f for f in os.listdir(processed_1500_dir) if f.lower().endswith('.jpg')])
    
    for f in renamed_files_1500:
        parts = f.split('-')
        num = parts[0]
        base_code = parts[1]
        lookup_key = base_code.lower()
        
        correct_subfolder_name = f"{num}-{base_code}"
        subfolder_path = os.path.join(combined_dir, correct_subfolder_name)
        
        # Check if a folder for this base_code already exists under a different name
        if lookup_key in existing_subs:
            old_name, old_path = existing_subs[lookup_key]
            if old_name != correct_subfolder_name:
                try:
                    os.rename(old_path, subfolder_path)
                    print(f"Renamed folder: {old_name} -> {correct_subfolder_name}")
                except Exception as e:
                    print(f"Could not rename folder {old_name} to {correct_subfolder_name}: {e}. Creating new folder.")
                    os.makedirs(subfolder_path, exist_ok=True)
        else:
            os.makedirs(subfolder_path, exist_ok=True)
            
        # Clear any existing files in this subfolder to prevent leftover old renames
        for item in os.listdir(subfolder_path):
            item_path = os.path.join(subfolder_path, item)
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                except Exception:
                    pass
        
        # Find original backup file path
        orig_backup_path_jpg = os.path.join(orig_backup_dir, f"{base_code}.JPG")
        orig_backup_path_png = os.path.join(orig_backup_dir, f"{base_code}.png")
        
        orig_src_path = None
        orig_ext = ".JPG"
        if os.path.exists(orig_backup_path_jpg):
            orig_src_path = orig_backup_path_jpg
        elif os.path.exists(orig_backup_path_png):
            orig_src_path = orig_backup_path_png
            orig_ext = ".png"
            
        dest_orig_path = os.path.join(subfolder_path, f"{num}-{base_code}-Original{orig_ext}")
        dest_1500_path = os.path.join(subfolder_path, f"{num}-{base_code}-Kohud-Kuhfell-Cowhide-Kuskinn-1500px.jpg")
        dest_orig_size_path = os.path.join(subfolder_path, f"{num}-{base_code}-Kohud-Kuhfell-Cowhide-Kuskinn-OriginalSize.jpg")
        
        # Copy files
        if orig_src_path:
            shutil.copy2(orig_src_path, dest_orig_path)
            
        src_1500 = os.path.join(processed_1500_dir, f)
        if os.path.exists(src_1500):
            shutil.copy2(src_1500, dest_1500_path)
            
        src_orig_size = os.path.join(processed_orig_dir, f)
        if os.path.exists(src_orig_size):
            shutil.copy2(src_orig_size, dest_orig_size_path)
            
    print("Combined Folders rebuilt successfully.")
    
    # 3. Create Rotated Verification Photos (unrotated camera perspective)
    print("\nGenerating Verification folder...")
    os.makedirs(verification_dir, exist_ok=True)
    for item in os.listdir(verification_dir):
        item_path = os.path.join(verification_dir, item)
        if os.path.isfile(item_path):
            try:
                os.remove(item_path)
            except Exception:
                pass
    
    verification_count = 0
    for filename, number in final_db.items():
        base = os.path.splitext(filename)[0]
        orig_path = os.path.join(orig_backup_dir, filename)
        if os.path.exists(orig_path):
            dest_file = os.path.join(verification_dir, f"{number}-{base}.jpg")
            # We copy and save unrotated because it is already right-side up relative to the camera
            img = Image.open(orig_path)
            img.convert('RGB').save(dest_file, format="JPEG", quality=85)
            verification_count += 1
            
    print(f"Generated {verification_count} verification photos in {verification_dir}.")

if __name__ == "__main__":
    main()
