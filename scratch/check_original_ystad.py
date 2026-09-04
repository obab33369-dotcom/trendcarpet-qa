import os
from PIL import Image

orig_ystad_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
target_folders = []

if os.path.exists(orig_ystad_dir):
    for f in os.listdir(orig_ystad_dir):
        if "19791" in f:
            target_folders.append(os.path.join(orig_ystad_dir, f))

print(f"Found {len(target_folders)} Ystad folders in original images:")
for folder in target_folders:
    print(f"\nFolder: {folder}")
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                fp = os.path.join(root, file)
                try:
                    with Image.open(fp) as img:
                        print(f"  {os.path.relpath(fp, folder)}: size={img.size}, bytes={os.path.getsize(fp)}")
                except Exception as e:
                    print(f"  Error reading {file}: {e}")
