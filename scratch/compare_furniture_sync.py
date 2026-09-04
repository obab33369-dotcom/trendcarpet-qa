import os
import re

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
CLEAN_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering")

def extract_sku(folder_name):
    m = re.search(r'\(([^)]+)\)$', folder_name)
    if m:
        return m.group(1).strip().lower()
    return None

def main():
    if not os.path.exists(CLEAN_SRC):
        print("Source folder does not exist.")
        return
    if not os.path.exists(CLEAN_DST):
        print("Destination folder does not exist.")
        return

    # Map SKUs to folders in both directories
    src_folders = {extract_sku(d): d for d in os.listdir(CLEAN_SRC) if os.path.isdir(os.path.join(CLEAN_SRC, d))}
    dst_folders = {extract_sku(d): d for d in os.listdir(CLEAN_DST) if os.path.isdir(os.path.join(CLEAN_DST, d))}
    
    missing_skus = []
    different_files = []
    total_files_in_src = 0
    total_missing_files = 0
    
    for sku, src_folder in src_folders.items():
        if not sku:
            continue
        src_path = os.path.join(CLEAN_SRC, src_folder)
        
        # Check recursively in source
        src_files = {}
        for r, ds, fs in os.walk(src_path):
            for f in fs:
                rel = os.path.relpath(os.path.join(r, f), src_path)
                src_files[rel] = os.path.join(r, f)
                total_files_in_src += 1
                
        if sku not in dst_folders:
            missing_skus.append(src_folder)
            total_missing_files += len(src_files)
            continue
            
        dst_folder = dst_folders[sku]
        dst_path = os.path.join(CLEAN_DST, dst_folder)
        
        # Check recursively in destination
        dst_files = {}
        for r, ds, fs in os.walk(dst_path):
            for f in fs:
                rel = os.path.relpath(os.path.join(r, f), dst_path)
                dst_files[rel] = os.path.join(r, f)
                
        # Compare files
        for rel in src_files:
            if rel not in dst_files:
                different_files.append((src_folder, rel, "missing"))
                total_missing_files += 1
            else:
                src_size = os.path.getsize(src_files[rel])
                dst_size = os.path.getsize(dst_files[rel])
                if src_size != dst_size:
                    different_files.append((src_folder, rel, "size_mismatch"))
                    
    print(f"Comparison Summary:")
    print(f"  Total furniture folders in source: {len(src_folders)}")
    print(f"  Total folders entirely missing in destination: {len(missing_skus)}")
    if missing_skus:
        print(f"    Sample missing folders: {missing_skus[:10]}")
    print(f"  Total files in source: {total_files_in_src}")
    print(f"  Total missing files in destination: {total_missing_files}")
    print(f"  Total size mismatches: {len([x for x in different_files if x[2] == 'size_mismatch'])}")
    
    if different_files:
        print(f"\nSample different/missing files:")
        for folder, rel, reason in different_files[:15]:
            print(f"  Folder: {folder} | File: {rel} | Reason: {reason}")

if __name__ == "__main__":
    main()
