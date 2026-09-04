import os
import numpy as np
from PIL import Image

artiklar_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_fixstolar\artiklar"

if not os.path.exists(artiklar_dir):
    print("Directory not found")
    sys.exit(0)

print("Scanning for potentially problematic chairs (no shadow or off-center):")
print("==========================================================================")

files = [f for f in os.listdir(artiklar_dir) if f.endswith(".jpg")]

for fn in sorted(files):
    path = os.path.join(artiklar_dir, fn)
    try:
        with Image.open(path) as img:
            arr = np.array(img.convert('RGB'))
            w, h = img.size
            
            # Find non-white pixels
            diff = np.sum(np.abs(arr.astype(int) - 255), axis=-1)
            non_white = diff > 15
            coords = np.argwhere(non_white)
            
            if coords.size > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                
                # Check solid body vs light shadow
                # Shadow pixels are usually light grey (diff between 15 and 100)
                # Chair body pixels are usually darker (diff > 100)
                shadow_pixels = (diff > 15) & (diff <= 100)
                solid_pixels = diff > 100
                
                shadow_count = np.sum(shadow_pixels)
                solid_count = np.sum(solid_pixels)
                
                # Calculate solid body center
                coords_solid = np.argwhere(solid_pixels)
                if coords_solid.size > 0:
                    ys_min, xs_min = coords_solid.min(axis=0)
                    ys_max, xs_max = coords_solid.max(axis=0)
                    solid_center = (xs_min + xs_max) / 2.0
                    solid_offset = solid_center - (w / 2.0)
                    solid_offset_pct = (solid_offset / w) * 100.0
                else:
                    solid_offset_pct = 0.0
                
                # Determine shadow status:
                # If very few shadow pixels are detected in the lower part of the image, it might lack a shadow
                # Let's count shadow pixels in the bottom 25% of the bounding box
                y_bottom_start = y_min + int(0.75 * (y_max - y_min))
                bottom_shadow = np.sum(shadow_pixels[y_bottom_start:y_max, :])
                
                # Issues flags
                issues = []
                if abs(solid_offset_pct) > 6.0:  # More than 6% off-center for the solid body
                    issues.append(f"Off-center ({solid_offset_pct:.1f}%)")
                if bottom_shadow < 200:  # Very few shadow pixels at the bottom
                    issues.append(f"Low/No shadow ({bottom_shadow} px)")
                    
                if issues:
                    print(f"File: {fn:30} | {', '.join(issues)}")
            else:
                print(f"File: {fn:30} | Empty image (no non-white pixels)")
    except Exception as e:
        print(f"File: {fn:30} | Error: {e}")
