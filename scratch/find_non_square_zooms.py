import os
import glob
from PIL import Image

zoom_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom"

if not os.path.exists(zoom_dir):
    print(f"Directory {zoom_dir} does not exist.")
    exit(1)

files = glob.glob(os.path.join(zoom_dir, "*.jpg"))
print(f"Found {len(files)} total files in zoom directory.")

non_square = []
for fpath in files:
    try:
        with Image.open(fpath) as img:
            w, h = img.size
            if w != h:
                non_square.append((fpath, w, h))
    except Exception as e:
        print(f"Error reading {fpath}: {e}")

print(f"\nFound {len(non_square)} non-square images:")
for fpath, w, h in non_square[:30]:
    print(f"  - Size: {w}x{h} | File: {os.path.basename(fpath)}")
    
if len(non_square) > 30:
    print(f"  ... and {len(non_square) - 30} more.")
