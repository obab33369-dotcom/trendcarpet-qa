import os
from PIL import Image
import random

FTP_UPLOAD_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload"
artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
liten_dir = os.path.join(artiklar_dir, "liten")
zoom_dir = os.path.join(artiklar_dir, "zoom")

def verify_folder(folder_path, expected_size):
    print(f"\nVerifying folder: {folder_path} (Expected: {expected_size}x{expected_size})")
    if not os.path.exists(folder_path):
        print("  [ERROR] Folder does not exist!")
        return
        
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    print(f"  Total files: {len(files)}")
    if not files:
        return
        
    sample = random.sample(files, min(len(files), 5))
    errors = 0
    for idx, f in enumerate(sample):
        p = os.path.join(folder_path, f)
        try:
            with Image.open(p) as img:
                w, h = img.size
                if w != expected_size or h != expected_size:
                    print(f"  [ERROR] Sample {idx+1} '{f}': Size is {w}x{h}!")
                    errors += 1
                else:
                    print(f"  [OK] Sample {idx+1} '{f}': {w}x{h}")
        except Exception as e:
            print(f"  [ERROR] Sample {idx+1} '{f}': Could not open! {e}")
            errors += 1
            
    if errors == 0:
        print(f"  [OK] All verified samples in {os.path.basename(folder_path)} are correct!")

verify_folder(artiklar_dir, 1000)
verify_folder(liten_dir, 400)
verify_folder(zoom_dir, 2000)
