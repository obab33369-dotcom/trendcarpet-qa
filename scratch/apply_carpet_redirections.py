import os
import json
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

def main():
    plan_path = os.path.join(PROJECT_DIR, "scratch", "carpet_redirection_plan.json")
    catalog_path = os.path.join(PROJECT_DIR, "scratch", "carpet_catalog.json")
    
    with open(plan_path, "r", encoding="utf-8") as f:
        redirections = json.load(f)
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    print("=== APPLYING VISUAL CARPET REDIRECTIONS ===")
    
    moved_count = 0
    skipped_count = 0
    
    for src_folder, files in redirections.items():
        src_dir = os.path.join(DISCARD_ROOT, src_folder)
        if not os.path.exists(src_dir):
            continue
            
        for fn, info in files.items():
            src_file = os.path.join(src_dir, fn)
            if not os.path.exists(src_file):
                continue
                
            matched_sku = info.get("matched_sku")
            if matched_sku:
                dest_info = catalog.get(matched_sku)
                if dest_info:
                    dest_folder = dest_info["folder_name"]
                    dest_dir = os.path.join(CLEAN_ROOT, dest_folder)
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    dest_file = os.path.join(dest_dir, fn)
                    
                    print(f"Moving: {src_folder}/{fn} -> {dest_folder}/{fn}")
                    shutil.move(src_file, dest_file)
                    moved_count += 1
                else:
                    print(f"Warning: SKU {matched_sku} not found in catalog for {src_folder}/{fn}")
                    skipped_count += 1
            else:
                print(f"Skipping (no match): {src_folder}/{fn} - Explanation: {info.get('explanation')[:80]}...")
                skipped_count += 1
                
    # Clean up empty source directories in both clean and discard roots
    print("\nCleaning up empty source folders...")
    cleaned_count = 0
    for folder in redirections.keys():
        for root_dir in [CLEAN_ROOT, DISCARD_ROOT]:
            folder_path = os.path.join(root_dir, folder)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Check if it contains only reference images
                files_left = os.listdir(folder_path)
                renders_left = [f for f in files_left if not f.startswith("00_REFERENCE_")]
                if not renders_left:
                    # Remove reference images first
                    for f in files_left:
                        try:
                            os.remove(os.path.join(folder_path, f))
                        except Exception:
                            pass
                    try:
                        os.rmdir(folder_path)
                        cleaned_count += 1
                        print(f"  Removed empty folder: {folder_path}")
                    except Exception:
                        pass
                        
    print(f"\n=== REDIRECTION RUN COMPLETE ===")
    print(f"Moved: {moved_count} files")
    print(f"Skipped: {skipped_count} files")
    print(f"Cleaned up: {cleaned_count} empty folders")

if __name__ == "__main__":
    main()
