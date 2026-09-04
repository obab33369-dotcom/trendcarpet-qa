import os

onedrive_root = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def scan_folders(root_dir):
    print(f"\nScanning: {root_dir}")
    if not os.path.exists(root_dir):
        print("  Directory does not exist.")
        return
        
    carpet_dirs = []
    for item in os.listdir(root_dir):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path) and ("matta" in item.lower() or "rug" in item.lower() or "rg01" in item.lower() or "angelholm" in item.lower() or "avendo" in item.lower() or "aranga" in item.lower()):
            carpet_dirs.append(item)
            
    if not carpet_dirs:
        print("  No carpet folders found.")
        return
        
    for item in sorted(carpet_dirs):
        path = os.path.join(root_dir, item)
        files = []
        for r, ds, fs in os.walk(path):
            for f in fs:
                if not f.startswith("00_REFERENCE_"):
                    rel = os.path.relpath(os.path.join(r, f), path)
                    files.append(rel)
        print(f"Folder: {item} ({len(files)} files)")
        for f in sorted(files):
            print(f"  - {f}")

for sub in os.listdir(onedrive_root):
    path = os.path.join(onedrive_root, sub)
    if os.path.isdir(path) and "sortering" in sub.lower():
        scan_folders(path)
