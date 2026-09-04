import os
import json
import re
import shutil
import stat
import sys

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def remove_readonly_onerror(func, path, excinfo):
    make_writable(path)
    try:
        func(path)
    except Exception as e:
        print(f"    Failed to delete {path}: {e}")

sys.path.append(PROJECT_DIR)
sys.path.append(os.path.join(PROJECT_DIR, "scratch"))
try:
    from rebuild_all_by_time import resolve_anchor, load_db
except Exception as e:
    print(f"Error importing helper functions: {e}")
    resolve_anchor = None
    load_db = None

def main():
    print("=== Applying Furniture Redirections ===")
    
    plan_path = os.path.join(PROJECT_DIR, "scratch", "furniture_redirection_plan.json")
    catalog_path = os.path.join(PROJECT_DIR, "scratch", "furniture_catalog.json")
    
    if not os.path.exists(plan_path) or not os.path.exists(catalog_path):
        print("Plan or Catalog JSON file not found.")
        return
        
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    # Load prompt databases
    batch1 = load_db("rooms_turboflow_batch1.json") if load_db else {}
    batch2 = load_db("rooms_turboflow_batch2.json") if load_db else {}
    full_catalog = load_db("rooms_turboflow_full_catalog.json") if load_db else {}
    
    db_mapping = {}
    db_mapping.update(batch1)
    db_mapping.update(batch2)
    db_mapping.update(full_catalog)
    
    moved_count = 0
    skipped_count = 0
    
    for orig_folder, files in plan.items():
        print(f"\nProcessing redirections from: {orig_folder}")
        
        for fn, res in files.items():
            if "error" in res or res.get("matched_sku") is None:
                skipped_count += 1
                continue
                
            matched_sku = res["matched_sku"]
            matched_name = res["matched_name"]
            
            if matched_sku not in catalog:
                print(f"  Warning: Matched SKU {matched_sku} not found in catalog. Skipped.")
                skipped_count += 1
                continue
                
            target_folder_name = catalog[matched_sku]["folder_name"]
            
            # Find file in discard root
            # (it might be in the main folder or a /reserv subfolder)
            src_path = os.path.join(DISCARD_ROOT, orig_folder, fn)
            if not os.path.exists(src_path):
                src_path = os.path.join(DISCARD_ROOT, orig_folder, "reserv", fn)
                
            if not os.path.exists(src_path):
                print(f"  Error: Source file {fn} not found in discard folder.")
                skipped_count += 1
                continue
                
            # Determine target subfolder (main or reserv) based on prompt database refs
            m = re.match(r"^(\d+)", fn)
            is_primary = True
            if m:
                prefix = int(m.group(1))
                if prefix in db_mapping:
                    refs = db_mapping[prefix]["refs"]
                    # Resolve refs
                    resolved_skus = []
                    for ref in refs:
                        if resolve_anchor:
                            sku, _ = resolve_anchor(ref)
                            if sku:
                                resolved_skus.append(sku)
                                
                    if matched_sku in resolved_skus:
                        idx = resolved_skus.index(matched_sku)
                        if idx > 0:
                            is_primary = False
                            
            # Setup target path
            if is_primary:
                target_dir = os.path.join(CLEAN_ROOT, target_folder_name)
            else:
                target_dir = os.path.join(CLEAN_ROOT, target_folder_name, "reserv")
                
            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, fn)
            
            # Make sure reference photo exists in target folder
            ref_path = catalog[matched_sku]["ref_path"]
            if ref_path and os.path.exists(ref_path):
                ref_fn = os.path.basename(ref_path)
                target_ref_dir = os.path.join(CLEAN_ROOT, target_folder_name)
                target_ref_path = os.path.join(target_ref_dir, ref_fn)
                if not os.path.exists(target_ref_path):
                    try:
                        make_writable(target_ref_dir)
                        shutil.copy2(ref_path, target_ref_path)
                        print(f"    Copied reference photo {ref_fn} to target folder.")
                    except Exception as e_copy:
                        print(f"    Warning: Could not copy reference: {e_copy}")
                        
            # Move file
            make_writable(src_path)
            make_writable(target_dir)
            try:
                # If target already exists, delete it first to avoid collision
                if os.path.exists(dest_path):
                    make_writable(dest_path)
                    os.remove(dest_path)
                shutil.move(src_path, dest_path)
                print(f"  Moved: {fn} -> {target_folder_name}{'' if is_primary else '/reserv'}")
                moved_count += 1
            except Exception as e:
                print(f"  Error moving {fn}: {e}")
                skipped_count += 1
                
    print(f"\nRedirection applied! Moved {moved_count} files, skipped/errors: {skipped_count}.")
    
    # 2. Cleanup Empty Folders
    print("\n=== Cleaning Up Empty Target Folders ===")
    folders_cleaned = 0
    
    for folder in plan.keys():
        for root in (CLEAN_ROOT, DISCARD_ROOT):
            dp = os.path.join(root, folder)
            if os.path.exists(dp) and os.path.isdir(dp):
                # Check for renders
                files = os.listdir(dp)
                renders = []
                for f in files:
                    fp = os.path.join(dp, f)
                    if os.path.isfile(fp) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        renders.append(f)
                        
                # Check for reserv folders
                reserv_path = os.path.join(dp, "reserv")
                has_reserv_renders = False
                if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
                    reserv_files = os.listdir(reserv_path)
                    for f in reserv_files:
                        fp = os.path.join(reserv_path, f)
                        if os.path.isfile(fp) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            has_reserv_renders = True
                            break
                            
                # If no renders are left in main or reserv, clean up the folder
                if not renders and not has_reserv_renders:
                    print(f"Cleaning empty folder: {dp}")
                    # Make all files and subdirectories writable
                    if os.path.exists(reserv_path):
                        for f in os.listdir(reserv_path):
                            make_writable(os.path.join(reserv_path, f))
                        make_writable(reserv_path)
                        
                    for f in files:
                        make_writable(os.path.join(dp, f))
                    make_writable(dp)
                    
                    try:
                        shutil.rmtree(dp, onerror=remove_readonly_onerror)
                        folders_cleaned += 1
                        print(f"  Successfully removed: {folder}")
                    except Exception as e:
                        print(f"  Error removing {folder}: {e}")
                        
    print(f"\nCleanup complete. Removed {folders_cleaned} empty directories.")

if __name__ == "__main__":
    main()
