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
    
    # Load raw mapping databases
    standard_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    rotated_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_rotated.json"
    
    with open(standard_json, 'r', encoding='utf-8') as f:
        std_db = json.load(f)
        
    with open(rotated_json, 'r', encoding='utf-8') as f:
        rot_db = json.load(f)
        
    # Manual corrections for number and rotation angle
    manual_data = {
        "BPQA5442.JPG": {"number": "669", "rotation_angle": 270},
        "OTYL1698.JPG": {"number": "352", "rotation_angle": 90},
        "RXSA5233.JPG": {"number": "727", "rotation_angle": 270},
        "OBSY6632.JPG": {"number": "832", "rotation_angle": 270},
        "AGJM5060.JPG": {"number": "355", "rotation_angle": 270},
        "WYGV2057.JPG": {"number": "625", "rotation_angle": 270},
        "NSPM3714.JPG": {"number": "352", "rotation_angle": 90},
        "HCHH1324.JPG": {"number": "258", "rotation_angle": 270},
        "DGJR8081.JPG": {"number": "258", "rotation_angle": 90},
        "KWHA5687.JPG": {"number": "259", "rotation_angle": 270},
        "YLBS5372.JPG": {"number": "259", "rotation_angle": 270},
        "AHIN4169.JPG": {"number": "336", "rotation_angle": 90},
        "CEYY6720.JPG": {"number": "492", "rotation_angle": 270},
        "CSKG8106.JPG": {"number": "345", "rotation_angle": 270},
        "CURC8337.JPG": {"number": "733", "rotation_angle": 270},
        "CZFW8641.JPG": {"number": "862", "rotation_angle": 270},
        "FUPG5453.JPG": {"number": "993", "rotation_angle": 270},
        "FWBU1032.JPG": {"number": "327", "rotation_angle": 270},
        "FZLK0753.JPG": {"number": "318", "rotation_angle": 90},
        "GDQV3716.JPG": {"number": "361", "rotation_angle": 270},
        "HRKU8965.JPG": {"number": "346", "rotation_angle": 90},
        "NNRK8041.JPG": {"number": "335", "rotation_angle": 90},
        "RDIK1368.JPG": {"number": "301", "rotation_angle": 270},
        "TNML9192.JPG": {"number": "241", "rotation_angle": 270},
        "VKTJ0424.JPG": {"number": "328", "rotation_angle": 90},
        "WKFI6689.JPG": {"number": "619", "rotation_angle": 270}
    }
    
    # Compile final database
    final_db = {}
    for filename in sorted(std_db.keys()):
        if filename.lower() == "c.jpg":
            continue
        base = os.path.splitext(filename)[0]
        
        # Start with standard DB values
        number = std_db[filename].get("number", "")
        angle = 0
        
        # Override with rotated DB values if they exist
        if filename in rot_db and "error" not in rot_db[filename]:
            number = rot_db[filename].get("number", number)
            angle = rot_db[filename].get("rotation_angle", 0)
            
        # Overwrite with manual verified values
        if filename in manual_data:
            number = manual_data[filename]["number"]
            angle = manual_data[filename]["rotation_angle"]
            
        final_db[filename] = {
            "number": number,
            "rotation_angle": angle
        }
        
    # Save final JSON
    final_json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_final.json"
    with open(final_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_db, f, indent=2, ensure_ascii=False)
    print(f"Saved final database of {len(final_db)} files to {final_json_path}")
    
    # 1. Clean up and rename files in processed folders
    print("\nRenaming files in Processed directories...")
    
    # We build a lookup: base_code (lowercase) -> correct_number
    lookup = {k.split('.')[0].lower(): v["number"] for k, v in final_db.items()}
    
    def rename_in_directory(directory):
        files = [f for f in os.listdir(directory) if f.lower().endswith('.jpg')]
        for f in files:
            # Parse prefix and code
            parts = f.split('-')
            if parts[0].isdigit():
                # Already prefixed with old number
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
                        # Avoid conflict if file exists
                        os.remove(old_path)
                    else:
                        os.rename(old_path, new_path)
                        
    rename_in_directory(processed_1500_dir)
    rename_in_directory(processed_orig_dir)
    print("Processed folders updated successfully.")
    
    # 2. Rebuild Combined Folders
    print("\nRebuilding Combined Folders...")
    os.makedirs(combined_dir, exist_ok=True)
    
    # We list the existing subfolders in combined_dir
    existing_subs = {}
    if os.path.exists(combined_dir):
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
                # Rename the folder
                try:
                    os.rename(old_path, subfolder_path)
                    print(f"Renamed folder: {old_name} -> {correct_subfolder_name}")
                except Exception as e:
                    print(f"Could not rename folder {old_name} to {correct_subfolder_name}: {e}. Creating new folder.")
                    os.makedirs(subfolder_path, exist_ok=True)
            else:
                pass
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
    
    # 3. Create Rotated Verification Photos
    print("\nGenerating Rotated Verification folder...")
    if os.path.exists(verification_dir):
        shutil.rmtree(verification_dir)
    os.makedirs(verification_dir, exist_ok=True)
    
    verification_count = 0
    for filename, info in final_db.items():
        base = os.path.splitext(filename)[0]
        number = info["number"]
        angle = info["rotation_angle"]
        
        orig_path = os.path.join(orig_backup_dir, filename)
        if os.path.exists(orig_path):
            img = Image.open(orig_path)
            if angle != 0:
                # Rotate counter-clockwise in Pillow to match clockwise rotation
                img_rotated = img.rotate(-angle, expand=True)
            else:
                img_rotated = img.copy()
                
            dest_file = os.path.join(verification_dir, f"{number}-{base}.jpg")
            # Convert to RGB and save as JPEG
            img_rotated.convert('RGB').save(dest_file, format="JPEG", quality=85)
            verification_count += 1
            
    print(f"Generated {verification_count} rotated photos in {verification_dir}.")

if __name__ == "__main__":
    main()
