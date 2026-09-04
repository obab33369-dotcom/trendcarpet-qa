import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def analyze_roots():
    roots = [
        "Reforma-Full-Catalog-sortering",
        "Reforma-Full-Catalog-sortering-borttagna",
        "Reforma-interiörer-ny-sortering",
        "Reforma-interiörer-ny-sortering-borttagna"
    ]
    
    for r in roots:
        path = os.path.join(ONEDRIVE_DIR, r)
        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            continue
            
        folders = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        carpets = [f for f in folders if is_carpet(f)]
        furniture = [f for f in folders if not is_carpet(f)]
        
        # Count total files inside carpet folders
        carpet_file_count = 0
        for cf in carpets:
            cf_path = os.path.join(path, cf)
            for root_dir, dirs, files in os.walk(cf_path):
                carpet_file_count += len([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
                
        print(f"Root: {r}")
        print(f"  Total directories: {len(folders)}")
        print(f"  Carpet directories: {len(carpets)}")
        print(f"  Furniture directories: {len(furniture)}")
        print(f"  Total image files in carpets: {carpet_file_count}")

if __name__ == "__main__":
    analyze_roots()
