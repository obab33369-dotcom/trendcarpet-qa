import os
import sys
import numpy as np
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def find_dark_borders(base_dir):
    print(f"Scanning directory: {base_dir}")
    if not os.path.exists(base_dir):
        print("Directory not found.")
        return
        
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                p_file = os.path.join(root, f)
                try:
                    with Image.open(p_file) as img:
                        arr = np.array(img.convert('RGB'))
                        h, w, _ = arr.shape
                        
                        top_border = arr[0:4, :, :]
                        bottom_border = arr[-4:, :, :]
                        left_border = arr[:, 0:4, :]
                        right_border = arr[:, -4:, :]
                        
                        dark_top = np.mean(top_border, axis=-1) < 100
                        dark_bottom = np.mean(bottom_border, axis=-1) < 100
                        dark_left = np.mean(left_border, axis=-1) < 100
                        dark_right = np.mean(right_border, axis=-1) < 100
                        
                        count_top = np.sum(dark_top)
                        count_bottom = np.sum(dark_bottom)
                        count_left = np.sum(dark_left)
                        count_right = np.sum(dark_right)
                        
                        total_dark = count_top + count_bottom + count_left + count_right
                        
                        if total_dark > 0:
                            print(f"  [DARK BORDER] {os.path.relpath(p_file, base_dir)}: found {total_dark} dark border pixels (Top={count_top}, Bottom={count_bottom}, Left={count_left}, Right={count_right})")
                            if count_top > 0:
                                y, x = np.argwhere(dark_top)[0]
                                print(f"    Sample top: y={y}, x={x}, RGB={list(top_border[y, x])}")
                            elif count_left > 0:
                                y, x = np.argwhere(dark_left)[0]
                                print(f"    Sample left: y={y}, x={x}, RGB={list(left_border[y, x])}")
                except Exception as e:
                    print(f"  Error reading {f}: {e}")

find_dark_borders(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v4")
