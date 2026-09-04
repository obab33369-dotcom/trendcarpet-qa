import os
import re
import shutil
import stat

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

CLEAN_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
DISCARD_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering-borttagna")

CLEAN_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering")
DISCARD_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering-borttagna")

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def extract_sku(folder_name):
    m = re.search(r'\(([^)]+)\)$', folder_name)
    if m:
        return m.group(1).strip().lower()
    return None

def build_sku_to_folder_map(root_dir):
    sku_map = {}
    if not os.path.exists(root_dir):
        return sku_map
        
    for item in os.listdir(root_dir):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path):
            sku = extract_sku(item)
            if sku:
                sku_map[sku] = item
    return sku_map

def sync_directories(src_root, dst_root):
    if not os.path.exists(src_root) or not os.path.exists(dst_root):
        print(f"Skipping sync: either {src_root} or {dst_root} does not exist.")
        return 0, 0
        
    print(f"\nSyncing: {os.path.basename(src_root)} -> {os.path.basename(dst_root)}")
    
    # Build maps of SKU -> Folder Name in both source and destination
    src_skus = build_sku_to_folder_map(src_root)
    dst_skus = build_sku_to_folder_map(dst_root)
    
    copied_files_count = 0
    new_folders_count = 0
    
    for sku, src_folder in src_skus.items():
        # Find matching destination folder name or create a new one using the source name
        if sku in dst_skus:
            dst_folder = dst_skus[sku]
        else:
            dst_folder = src_folder
            new_folders_count += 1
            
        src_folder_path = os.path.join(src_root, src_folder)
        dst_folder_path = os.path.join(dst_root, dst_folder)
        
        # Sync files directly in the product folder (Primary files and references)
        os.makedirs(dst_folder_path, exist_ok=True)
        make_writable(dst_folder_path)
        
        for item in os.listdir(src_folder_path):
            src_file_path = os.path.join(src_folder_path, item)
            if os.path.isfile(src_file_path):
                dst_file_path = os.path.join(dst_folder_path, item)
                if not os.path.exists(dst_file_path):
                    try:
                        shutil.copy2(src_file_path, dst_file_path)
                        copied_files_count += 1
                    except Exception as e:
                        print(f"      Error copying {item}: {e}")
                        
        # Sync files in /reserv folder
        src_reserv_path = os.path.join(src_folder_path, "reserv")
        if os.path.exists(src_reserv_path) and os.path.isdir(src_reserv_path):
            dst_reserv_path = os.path.join(dst_folder_path, "reserv")
            os.makedirs(dst_reserv_path, exist_ok=True)
            make_writable(dst_reserv_path)
            
            for item in os.listdir(src_reserv_path):
                src_file_path = os.path.join(src_reserv_path, item)
                if os.path.isfile(src_file_path):
                    dst_file_path = os.path.join(dst_reserv_path, item)
                    if not os.path.exists(dst_file_path):
                        try:
                            shutil.copy2(src_file_path, dst_file_path)
                            copied_files_count += 1
                        except Exception as e:
                            print(f"      Error copying {item} in reserv: {e}")
                            
    return copied_files_count, new_folders_count

def main():
    print("=== SYNCHRONIZING DETECTED FURNITURE AND CARPET RENDERS TO CONSOLIDATED FOLDER ===")
    
    clean_copied, clean_new_dirs = sync_directories(CLEAN_SRC, CLEAN_DST)
    discard_copied, discard_new_dirs = sync_directories(DISCARD_SRC, DISCARD_DST)
    
    print("\n" + "="*80)
    print("SYNC SUMMARY:")
    print(f"  Approved folder: Copied {clean_copied} files, Created {clean_new_dirs} new product folders.")
    print(f"  Discarded folder: Copied {discard_copied} files, Created {discard_new_dirs} new product folders.")
    print("="*80)

if __name__ == "__main__":
    main()
