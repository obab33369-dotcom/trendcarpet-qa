import os
import shutil
import sys
import json
import re

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
WORKSPACE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

TEST_TOPAZ_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
BATCH2_SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter"

def optimize_batch(batch_num, num_parts, master_src_dir, filename_pattern_json, folder_pattern_od):
    print(f"\n--- OPTIMIZING BATCH {batch_num} FOLDERS ---")
    
    # Pre-scan source directory to build ID-to-full-filename mapping
    id_to_full = {}
    if os.path.exists(master_src_dir):
        for f_name in os.listdir(master_src_dir):
            base, _ = os.path.splitext(f_name)
            match = re.match(r'^(\d+)_', base)
            if match:
                num_id = match.group(1)
                id_to_full[num_id] = f_name
                
    print(f"  [INFO] Pre-scanned source folder. Built ID mapping for {len(id_to_full)} products.")
    
    for p in range(1, num_parts + 1):
        json_filename = filename_pattern_json.format(p)
        json_path = os.path.join(WORKSPACE_DIR, json_filename)
        
        if not os.path.exists(json_path):
            print(f"  [ERROR] Prompt JSON file not found: {json_path}")
            continue
            
        with open(json_path, "r", encoding="utf-8") as f:
            rows = json.load(f)
            
        # Collect all unique image references in this part
        referenced_images = set()
        unmapped_count = 0
        
        for r in rows:
            img_refs_str = r.get("image_references", "")
            if img_refs_str:
                parts = [x.strip() for x in img_refs_str.split(";") if x.strip()]
                for p_img in parts:
                    if batch_num == 2:
                        # For Batch 2, references are short names like '1786.png'
                        # Extract the numeric ID
                        base, _ = os.path.splitext(p_img)
                        match = re.match(r'^(\d+)', base)
                        if match:
                            num_id = match.group(1)
                            if num_id in id_to_full:
                                referenced_images.add(id_to_full[num_id])
                            else:
                                unmapped_count += 1
                        else:
                            unmapped_count += 1
                    else:
                        # Batch 1 already uses full filenames
                        referenced_images.add(p_img)
                        
        if unmapped_count > 0:
            print(f"  [WARNING] Part {p}: {unmapped_count} references could not be mapped to physical files!")
            
        print(f"  Part {p}: Found {len(rows)} prompts referencing {len(referenced_images)} unique images.")
        
        # Prepare destination folder
        dest_folder_name = folder_pattern_od.format(p)
        dest_path = os.path.join(ONEDRIVE_DIR, dest_folder_name)
        os.makedirs(dest_path, exist_ok=True)
        
        # List current files in dest folder to clean them up
        current_files = os.listdir(dest_path)
        
        # Delete files that are NOT referenced anymore
        deleted_count = 0
        for f_name in current_files:
            if f_name not in referenced_images:
                try:
                    os.unlink(os.path.join(dest_path, f_name))
                    deleted_count += 1
                except Exception as e:
                    print(f"    Failed to delete {f_name}: {e}")
                    
        # Copy missing files that ARE referenced
        copied_count = 0
        missing_count = 0
        for f_name in sorted(referenced_images):
            src_file_path = os.path.join(master_src_dir, f_name)
            dest_file_path = os.path.join(dest_path, f_name)
            
            # If the file already exists in dest, skip copying
            if os.path.exists(dest_file_path):
                continue
                
            if os.path.exists(src_file_path):
                try:
                    shutil.copy2(src_file_path, dest_file_path)
                    copied_count += 1
                except Exception as e:
                    print(f"    Failed to copy {f_name}: {e}")
            else:
                # Search case-insensitively just in case
                found_match = False
                f_name_lower = f_name.lower()
                for actual_name in os.listdir(master_src_dir):
                    if actual_name.lower() == f_name_lower:
                        shutil.copy2(os.path.join(master_src_dir, actual_name), dest_file_path)
                        copied_count += 1
                        found_match = True
                        break
                        
                if not found_match:
                    print(f"    [WARNING] Reference image not found in source: {f_name}")
                    missing_count += 1
                    
        # Final count in folder
        final_files_count = len(os.listdir(dest_path))
        print(f"    -> Done! Folder {dest_folder_name} now contains exactly {final_files_count} images.")
        print(f"       (Cleaned/Deleted: {deleted_count}, Newly Copied: {copied_count}, Missing in source: {missing_count})")

def main():
    # Batch 1 (8 parts)
    optimize_batch(
        batch_num=1,
        num_parts=8,
        master_src_dir=TEST_TOPAZ_DIR,
        filename_pattern_json="turboflow_ready_batch1_del{}.json",
        folder_pattern_od="turboflow_batch1_produkter_aktiva_del{}"
    )
    
    # Batch 2 (2 parts)
    optimize_batch(
        batch_num=2,
        num_parts=2,
        master_src_dir=BATCH2_SRC_DIR,
        filename_pattern_json="turboflow_ready_batch2_del{}.json",
        folder_pattern_od="turboflow_batch2_produkter_aktiva_del{}"
    )

if __name__ == "__main__":
    main()
