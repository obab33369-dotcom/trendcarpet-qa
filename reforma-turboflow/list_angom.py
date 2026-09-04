import os

ORIG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]

print("Folders containing 'ngom':")
for folder in orig_folders:
    if "ngom" in folder.lower() or "ngom" in folder.encode('utf-8', errors='ignore').decode('utf-8').lower():
        print(f"  {repr(folder)}")
