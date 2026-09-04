import os
import re

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
CLEAN_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def extract_sku(folder_name):
    m = re.search(r'\(([^)]+)\)$', folder_name)
    if m:
        return m.group(1).strip().lower()
    return None

def main():
    if not os.path.exists(CLEAN_SRC) or not os.path.exists(CLEAN_DST):
        print("Required folders do not exist.")
        return
        
    src_skus = {extract_sku(d): d for d in os.listdir(CLEAN_SRC) if os.path.isdir(os.path.join(CLEAN_SRC, d))}
    
    extra_furniture_folders = []
    extra_furniture_files = []
    
    for item in os.listdir(CLEAN_DST):
        path = os.path.join(CLEAN_DST, item)
        if os.path.isdir(path):
            if is_carpet(item):
                # Skip carpets since they are handled separately
                continue
                
            sku = extract_sku(item)
            if not sku:
                print(f"Non-SKU folder in destination: {item}")
                continue
                
            if sku not in src_skus:
                extra_furniture_folders.append(item)
                # Count files recursively
                for r, ds, fs in os.walk(path):
                    for f in fs:
                        extra_furniture_files.append(os.path.join(r, f))
                continue
                
            # If the folder exists in both, check for files in destination that are not in source
            src_folder = src_skus[sku]
            src_path = os.path.join(CLEAN_SRC, src_folder)
            
            src_files = set()
            for r, ds, fs in os.walk(src_path):
                for f in fs:
                    src_files.add(os.path.relpath(os.path.join(r, f), src_path))
                    
            for r, ds, fs in os.walk(path):
                for f in fs:
                    rel = os.path.relpath(os.path.join(r, f), path)
                    if rel not in src_files:
                        extra_furniture_files.append(os.path.join(r, f))
                        
    print("Orphan/Extra furniture elements in Reforma-interiörer-ny-sortering:")
    print(f"  Extra folders: {len(extra_furniture_folders)}")
    if extra_furniture_folders:
        print(f"    Sample: {extra_furniture_folders[:10]}")
    print(f"  Extra files (including inside extra folders): {len(extra_furniture_files)}")
    if extra_furniture_files:
        print(f"    Sample files:")
        for f in extra_furniture_files[:20]:
            print(f"      {os.path.relpath(f, CLEAN_DST)}")

if __name__ == "__main__":
    main()
