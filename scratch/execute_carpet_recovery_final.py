import os
import re
import shutil
import json
import collections

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

# 1. Load mappings and DB
from test_fixed_resolver_v2 import final_resolve_anchor, clean_ref, get_beautiful_name

db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")
with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

# Index database by prefix
full_catalog = {}
for item in db:
    prompt = item.get('prompt', '')
    m = re.match(r'^(\d+)\s*-', prompt)
    if m:
        idx = int(m.group(1))
        full_catalog[idx] = {
            "refs": [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
        }

def clean_folder_name(name):
    return re.sub(r'[\\/*?:\'\"<>|]', '', name).strip()

def get_product_folder_name(sku, name):
    return clean_folder_name(f"{name} ({sku})")

def main():
    print("=== STARTING SURGICAL CARPET RECOVERY AND CLEANUP ===")
    
    # Track files to copy and delete
    # Key: src_path -> Value: list of dest_paths to copy to
    copies_to_make = collections.defaultdict(list)
    deletes_to_make = set()
    
    # Track reference images to copy to the new carpet folders
    carpets_to_copy_ref = set()
    
    # 2. Scan both Clean and Discard directories
    for root_dir in [CLEAN_DIR, DISCARD_DIR]:
        if not os.path.exists(root_dir):
            continue
            
        print(f"Scanning directory: {root_dir}")
        for folder in os.listdir(root_dir):
            folder_path = os.path.join(root_dir, folder)
            if not os.path.isdir(folder_path):
                continue
                
            # Parse SKU from folder name
            m_sku = re.search(r'\(([^)]+)\)$', folder)
            folder_sku = m_sku.group(1) if m_sku else None
            
            # Scan files in main folder
            for f in os.listdir(folder_path):
                f_path = os.path.join(folder_path, f)
                if os.path.isfile(f_path) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                    m_idx = re.match(r'^(\d+)-', f)
                    if m_idx:
                        idx = int(m_idx.group(1))
                        if idx in full_catalog:
                            # Resolve correct SKUs for this index
                            correct_skus = []
                            refs = full_catalog[idx]["refs"]
                            for ref_idx, ref in enumerate(refs):
                                sku, name = final_resolve_anchor(ref)
                                if sku:
                                    correct_skus.append((sku, name, ref_idx))
                                    
                            correct_folder_skus = set(item[0] for item in correct_skus)
                            
                            # Check if the folder we found this in is correct
                            if folder_sku not in correct_folder_skus:
                                print(f"Found misclassified file: {f} in folder: {folder} (SKU: {folder_sku})")
                                deletes_to_make.add(f_path)
                                
                            # Plan copies to the correct folders
                            for sku, name, ref_idx in correct_skus:
                                dest_folder_name = get_product_folder_name(sku, name)
                                if sku.startswith("RG01") or "matta" in name.lower() or "rug" in name.lower():
                                    carpets_to_copy_ref.add((sku, name))
                                    
                                if ref_idx == 0:
                                    dest_path = os.path.join(root_dir, dest_folder_name, f)
                                else:
                                    dest_path = os.path.join(root_dir, dest_folder_name, "reserv", f)
                                    
                                if not os.path.exists(dest_path):
                                    copies_to_make[f_path].append(dest_path)
                                    
            # Scan files in reserv folder
            reserv_path = os.path.join(folder_path, "reserv")
            if os.path.exists(reserv_path):
                for f in os.listdir(reserv_path):
                    f_path = os.path.join(reserv_path, f)
                    if os.path.isfile(f_path) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                        m_idx = re.match(r'^(\d+)-', f)
                        if m_idx:
                            idx = int(m_idx.group(1))
                            if idx in full_catalog:
                                correct_skus = []
                                refs = full_catalog[idx]["refs"]
                                for ref_idx, ref in enumerate(refs):
                                    sku, name = final_resolve_anchor(ref)
                                    if sku:
                                        correct_skus.append((sku, name, ref_idx))
                                        
                                correct_folder_skus = set(item[0] for item in correct_skus)
                                
                                if folder_sku not in correct_folder_skus:
                                    print(f"Found misclassified file in reserv: {f} in folder: {folder}/reserv (SKU: {folder_sku})")
                                    deletes_to_make.add(f_path)
                                    
                                for sku, name, ref_idx in correct_skus:
                                    dest_folder_name = get_product_folder_name(sku, name)
                                    if sku.startswith("RG01") or "matta" in name.lower() or "rug" in name.lower():
                                        carpets_to_copy_ref.add((sku, name))
                                        
                                    if ref_idx == 0:
                                        dest_path = os.path.join(root_dir, dest_folder_name, f)
                                    else:
                                        dest_path = os.path.join(root_dir, dest_folder_name, "reserv", f)
                                        
                                    if not os.path.exists(dest_path):
                                        copies_to_make[f_path].append(dest_path)

    print(f"\nPlanned {sum(len(v) for v in copies_to_make.values())} file copies.")
    print(f"Planned {len(deletes_to_make)} file deletions.")
    
    # 3. Perform copies first to prevent data loss
    copied_count = 0
    for src, dests in copies_to_make.items():
        if os.path.exists(src):
            for dest in dests:
                try:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)
                    copied_count += 1
                except Exception as e:
                    print(f"Error copying {src} to {dest}: {e}")
                    
    print(f"Successfully copied {copied_count} files to their correct folders.")
    
    # Copy reference photos for carpets if they don't exist
    ref_copied = 0
    for sku, name in carpets_to_copy_ref:
        dest_folder_name = get_product_folder_name(sku, name)
        for root_dir in [CLEAN_DIR, DISCARD_DIR]:
            product_folder = os.path.join(root_dir, dest_folder_name)
            if os.path.exists(product_folder):
                # Check if 00_REFERENCE exists
                has_ref = any(f.startswith("00_REFERENCE_") for f in os.listdir(product_folder))
                if not has_ref:
                    # Find reference source
                    ref_src_paths = [
                        os.path.join(WORKSPACE_DIR, "reforma-original-images", f"{sku}.jpg"),
                        os.path.join(WORKSPACE_DIR, "reforma-original-images", f"{sku}.png"),
                        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{sku}.jpg"),
                        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{sku}.png")
                    ]
                    for path in ref_src_paths:
                        if os.path.exists(path):
                            ext = os.path.splitext(path)[1]
                            dest = os.path.join(product_folder, f"00_REFERENCE_{sku}{ext}")
                            try:
                                shutil.copy2(path, dest)
                                ref_copied += 1
                                break
                            except Exception:
                                pass
                                
    print(f"Copied {ref_copied} reference photos to carpet folders.")
    
    # 4. Perform deletions of incorrect files
    deleted_count = 0
    for path in deletes_to_make:
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {path}: {e}")
                
    print(f"Successfully deleted {deleted_count} misclassified files from incorrect folders.")
    
    # 5. Clean up empty folders on OneDrive (e.g. empty reserv folders)
    cleaned_dirs = 0
    for root_dir in [CLEAN_DIR, DISCARD_DIR]:
        if not os.path.exists(root_dir):
            continue
        for folder in os.listdir(root_dir):
            folder_path = os.path.join(root_dir, folder)
            if not os.path.isdir(folder_path):
                continue
                
            reserv_path = os.path.join(folder_path, "reserv")
            if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
                if not os.listdir(reserv_path):
                    try:
                        os.rmdir(reserv_path)
                        cleaned_dirs += 1
                    except Exception:
                        pass
                        
            # If main folder is empty or only has the reference photo, delete it (unless it is clean folder and we want to keep it)
            remaining_renders = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith("00_REFERENCE_")]
            has_reserv = os.path.exists(os.path.join(folder_path, "reserv"))
            
            if not remaining_renders and not has_reserv:
                try:
                    shutil.rmtree(folder_path)
                    cleaned_dirs += 1
                except Exception:
                    pass
                    
    print(f"Cleaned up {cleaned_dirs} empty folders/subfolders.")
    print("=== RECOVERY COMPLETE ===")

if __name__ == "__main__":
    main()
