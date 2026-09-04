import os

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
clean_dir = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")

if os.path.exists(clean_dir):
    folders = sorted([d for d in os.listdir(clean_dir) if os.path.isdir(os.path.join(clean_dir, d))])
    print(f"Total folders: {len(folders)}")
    print("Folders containing 'Matta' or 'rug' or 'RG0':")
    for f in folders:
        f_lower = f.lower()
        if "matta" in f_lower or "rug" in f_lower or "rg0" in f_lower or "jute" in f_lower:
            print(f"  {f}")
else:
    print(f"Directory does not exist: {clean_dir}")
