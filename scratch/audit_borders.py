import os
import sys
from PIL import Image
import numpy as np

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

dest_artiklar = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-18-FTP\artiklar"

if not os.path.exists(dest_artiklar):
    print("FTP artiklar folder not found.")
    exit(1)

image_files = [f for f in os.listdir(dest_artiklar) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
print(f"Auditing outer border pixels for {len(image_files)} files in: {dest_artiklar}")

success_count = 0
fail_count = 0

for idx, f in enumerate(image_files):
    p_file = os.path.join(dest_artiklar, f)
    try:
        with Image.open(p_file) as img:
            arr = np.array(img.convert('RGB'))
            h, w, _ = arr.shape
            
            # Extract 1px wide boundary vectors
            top_row = arr[0, :, :]
            bottom_row = arr[-1, :, :]
            left_col = arr[:, 0, :]
            right_col = arr[:, -1, :]
            
            # Check for non-white pixels (where any channel is less than 255)
            non_white_top = np.any(top_row < 255, axis=-1)
            non_white_bottom = np.any(bottom_row < 255, axis=-1)
            non_white_left = np.any(left_col < 255, axis=-1)
            non_white_right = np.any(right_col < 255, axis=-1)
            
            non_white_total = (np.sum(non_white_top) + np.sum(non_white_bottom) + 
                               np.sum(non_white_left) + np.sum(non_white_right))
            
            if non_white_total > 0:
                print(f"  ❌ {f} HAS non-white border pixels! (Total non-white edge pixels: {non_white_total})")
                
                # Check min/max colors of the non-white pixels to see what they are
                all_edge_pixels = np.concatenate([top_row, bottom_row, left_col, right_col], axis=0)
                non_white_mask = np.any(all_edge_pixels < 255, axis=-1)
                non_white_colors = all_edge_pixels[non_white_mask]
                print(f"    Min edge pixel color: {np.min(non_white_colors, axis=0)}, Mean: {np.mean(non_white_colors, axis=0).astype(int)}")
                fail_count += 1
            else:
                print(f"  ✓ {f}: Border is 100% pure white.")
                success_count += 1
    except Exception as e:
        print(f"  Error reading {f}: {e}")

print("--------------------------------------------------")
print(f"Audit Complete! clean: {success_count}, with edge artifacts: {fail_count}")
print("==================================================")
