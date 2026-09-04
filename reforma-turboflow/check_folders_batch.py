import os

root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
if os.path.exists(root_dir):
    dirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    print("Folders containing 'batch' or 'turboflow':")
    for d in sorted(dirs):
        if "batch" in d.lower() or "turboflow" in d.lower():
            print(f"  {d}")
else:
    print("OneDrive pictures directory not found.")
