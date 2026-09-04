import os
import re

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering")
DISCARD_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering-borttagna")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def extract_sku(folder_name):
    m = re.search(r'\(([^)]+)\)$', folder_name)
    if m:
        return m.group(1).strip()
    return None

def audit_directory(root_dir):
    print(f"\nAuditing carpet folders in {os.path.basename(root_dir)}:")
    if not os.path.exists(root_dir):
        print("Directory does not exist.")
        return
        
    carpet_folders = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d)) and is_carpet(d)]
    print(f"Total carpet folders found: {len(carpet_folders)}")
    
    empty_folders = []
    folders_without_ref = []
    folders_with_ref = []
    has_reserv = []
    
    for folder in sorted(carpet_folders):
        path = os.path.join(root_dir, folder)
        files = os.listdir(path)
        sku = extract_sku(folder)
        
        # count image files
        images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and not f.startswith('00_REFERENCE_')]
        ref_files = [f for f in files if f.startswith('00_REFERENCE_')]
        
        # check if reserv subfolder exists
        reserv_path = os.path.join(path, "reserv")
        reserv_files_count = 0
        if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
            reserv_files_count = len([f for f in os.listdir(reserv_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
            has_reserv.append((folder, reserv_files_count))
            
        total_renders = len(images) + reserv_files_count
        
        if total_renders == 0:
            empty_folders.append(folder)
        
        if ref_files:
            folders_with_ref.append((folder, ref_files[0]))
        else:
            folders_without_ref.append(folder)
            
    print(f"Folders with renderings: {len(carpet_folders) - len(empty_folders)}")
    print(f"Empty folders (no renders): {len(empty_folders)}")
    if empty_folders:
        print(f"  Sample empty folders: {empty_folders[:5]}")
        
    print(f"Folders with reference image: {len(folders_with_ref)}")
    print(f"Folders without reference image: {len(folders_without_ref)}")
    if folders_without_ref:
        print(f"  Sample without ref: {folders_without_ref[:10]}")
        
    print(f"Folders with reserv subfolders: {len(has_reserv)}")
    if has_reserv:
        print(f"  Sample with reserv: {has_reserv[:5]}")

if __name__ == "__main__":
    audit_directory(CLEAN_DST)
    audit_directory(DISCARD_DST)
