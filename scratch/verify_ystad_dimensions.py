import os
from PIL import Image

dir_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2"
artiklar_dir = os.path.join(dir_path, "artiklar")
liten_dir = os.path.join(artiklar_dir, "liten")
zoom_dir = os.path.join(artiklar_dir, "zoom")

print("--- Artiklar ---")
for f in sorted(os.listdir(artiklar_dir)):
    if f.lower().endswith(".jpg") and os.path.isfile(os.path.join(artiklar_dir, f)):
        img_path = os.path.join(artiklar_dir, f)
        print(f"  {f}: {Image.open(img_path).size}")

print("\n--- Liten ---")
for f in sorted(os.listdir(liten_dir)):
    if f.lower().endswith(".jpg"):
        img_path = os.path.join(liten_dir, f)
        print(f"  {f}: {Image.open(img_path).size}")

print("\n--- Zoom ---")
for f in sorted(os.listdir(zoom_dir)):
    if f.lower().endswith(".jpg"):
        img_path = os.path.join(zoom_dir, f)
        print(f"  {f}: {Image.open(img_path).size}")
