import os
import json
import shutil

def load_mapping():
    path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create lookup: base_name (lowercase) -> number
    lookup = {}
    for filename, val in data.items():
        if "error" in val:
            continue
        base = os.path.splitext(filename)[0].lower()
        lookup[base] = str(val.get("number", "")).strip()
    return lookup

def process_directories(dry_run=True):
    lookup = load_mapping()
    if not lookup:
        print("Error: No mapping found.")
        return
        
    base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides"
    orig_backup_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    
    processed_1500_dir = os.path.join(base_dir, "Batch 2 - Processed (1500x1500)")
    processed_orig_dir = os.path.join(base_dir, "Batch 2 - Processed (Original Size)")
    combined_dir = os.path.join(base_dir, "Batch 2 - Combined Folders")
    
    # Check source folders
    if not os.path.exists(processed_1500_dir) or not os.path.exists(processed_orig_dir):
        print("Error: Source processed directories do not exist.")
        return
        
    if not dry_run:
        os.makedirs(combined_dir, exist_ok=True)
        
    print(f"Starting processing... (Dry Run: {dry_run})")
    
    # List of base files
    files_1500 = sorted([f for f in os.listdir(processed_1500_dir) if f.lower().endswith('.jpg')])
    
    success_count = 0
    
    for f in files_1500:
        # File name is like: AHIN4169-Kohud-Kuhfell-Cowhide-Kuskinn.jpg
        parts = f.split('-')
        if parts[0].isdigit():
            print(f"Skipping already renamed file: {f}")
            continue
            
        base_code = parts[0]
        lookup_key = base_code.lower()
        
        if lookup_key not in lookup:
            print(f"Warning: No ID found for code {base_code} in file {f}")
            continue
            
        num = lookup[lookup_key]
        if not num:
            print(f"Warning: Empty ID for code {base_code}")
            continue
            
        # Renamed filenames in their respective processed folders
        renamed_1500_name = f"{num}-{f}"
        renamed_orig_name = f"{num}-{f}"
        
        old_1500_path = os.path.join(processed_1500_dir, f)
        new_1500_path = os.path.join(processed_1500_dir, renamed_1500_name)
        
        old_orig_path = os.path.join(processed_orig_dir, f)
        new_orig_path = os.path.join(processed_orig_dir, renamed_orig_name)
        
        # Original backup file path
        orig_backup_path_jpg = os.path.join(orig_backup_dir, f"{base_code}.JPG")
        orig_backup_path_jpeg = os.path.join(orig_backup_dir, f"{base_code}.jpeg")
        orig_backup_path_png = os.path.join(orig_backup_dir, f"{base_code}.png")
        
        orig_src_path = None
        orig_ext = ".JPG"
        if os.path.exists(orig_backup_path_jpg):
            orig_src_path = orig_backup_path_jpg
            orig_ext = ".JPG"
        elif os.path.exists(orig_backup_path_jpeg):
            orig_src_path = orig_backup_path_jpeg
            orig_ext = ".jpeg"
        elif os.path.exists(orig_backup_path_png):
            orig_src_path = orig_backup_path_png
            orig_ext = ".png"
            
        # Destination subfolder inside Combined Folders
        subfolder_name = f"{num}-{base_code}"
        subfolder_path = os.path.join(combined_dir, subfolder_name)
        
        # Files inside the subfolder
        dest_orig_path = os.path.join(subfolder_path, f"{num}-{base_code}-Original{orig_ext}")
        dest_1500_path = os.path.join(subfolder_path, f"{num}-{base_code}-Kohud-Kuhfell-Cowhide-Kuskinn-1500px.jpg")
        dest_orig_size_path = os.path.join(subfolder_path, f"{num}-{base_code}-Kohud-Kuhfell-Cowhide-Kuskinn-OriginalSize.jpg")
        
        if dry_run:
            print(f"[DRY-RUN] Create Folder: {subfolder_name}")
            if orig_src_path:
                print(f"  Copy Original: {os.path.basename(orig_src_path)} -> {os.path.basename(dest_orig_path)}")
            else:
                print(f"  Warning: Original photo not found for {base_code}")
            print(f"  Rename & Copy 1500px: '{f}' -> '{renamed_1500_name}' (And copy to subfolder as {os.path.basename(dest_1500_path)})")
            print(f"  Rename & Copy OrigSize: '{f}' -> '{renamed_orig_name}' (And copy to subfolder as {os.path.basename(dest_orig_size_path)})")
        else:
            try:
                # 1. Create subfolder
                os.makedirs(subfolder_path, exist_ok=True)
                
                # 2. Copy original raw photo to subfolder
                if orig_src_path:
                    shutil.copy2(orig_src_path, dest_orig_path)
                
                # 3. Copy processed Original Size file to subfolder
                if os.path.exists(old_orig_path):
                    shutil.copy2(old_orig_path, dest_orig_size_path)
                    # Rename the file in the processed Original Size directory
                    os.rename(old_orig_path, new_orig_path)
                    
                # 4. Copy processed 1500x1500px file to subfolder
                if os.path.exists(old_1500_path):
                    shutil.copy2(old_1500_path, dest_1500_path)
                    # Rename the file in the processed 1500x1500px directory
                    os.rename(old_1500_path, new_1500_path)
                
                success_count += 1
            except Exception as e:
                print(f"Error processing {base_code}: {e}")
                
    if not dry_run:
        print(f"\nCompleted! Successfully processed {success_count} cowhide folders.")

def main():
    print("=== STARTING ACTIVE RUN ===")
    process_directories(dry_run=False)

if __name__ == "__main__":
    main()
