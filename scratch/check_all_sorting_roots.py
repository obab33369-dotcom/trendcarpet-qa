import os

onedrive_root = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

for name in sorted(os.listdir(onedrive_root)):
    path = os.path.join(onedrive_root, name)
    if os.path.isdir(path) and "sortering" in name.lower():
        # count total files recursively
        count = 0
        carpet_folders = 0
        furniture_folders = 0
        for r, ds, fs in os.walk(path):
            count += len([f for f in fs if not f.startswith("00_REFERENCE_")])
            if r == path:
                for d in ds:
                    d_lower = d.lower()
                    if "matta" in d_lower or "rug" in d_lower or "rg01" in d_lower or "angelholm" in d_lower or "avendo" in d_lower or "aranga" in d_lower:
                        carpet_folders += 1
                    else:
                        furniture_folders += 1
                        
        print(f"Directory: {name}")
        print(f"  Total renders: {count}")
        print(f"  Carpet folders: {carpet_folders}")
        print(f"  Furniture folders: {furniture_folders}")
        print("-" * 50)
