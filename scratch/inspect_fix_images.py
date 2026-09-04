import os
from PIL import Image

fix_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"
print("Scanning some files in Refoma white background fix...")

count = 0
for root, dirs, files in os.walk(fix_dir):
    for filename in files:
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            full_path = os.path.join(root, filename)
            try:
                with Image.open(full_path) as img:
                    print(f"Path: {full_path}")
                    print(f"  Size: {img.size} | Mode: {img.mode}")
            except Exception as e:
                print(f"  Error reading {filename}: {e}")
            count += 1
            if count >= 10:
                break
    if count >= 10:
        break
