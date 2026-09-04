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

for f in ["1200180.jpg", "37281105.jpg"]:
    p_file = os.path.join(dest_artiklar, f)
    if not os.path.exists(p_file):
        print(f"File not found: {p_file}")
        continue
    
    with Image.open(p_file) as img:
        arr = np.array(img.convert('RGB'))
        h, w, _ = arr.shape
        print(f"\nAnalyzing {f}: size={w}x{h}")
        
        # Check borders
        top = arr[0, :, :]
        bottom = arr[-1, :, :]
        left = arr[:, 0, :]
        right = arr[:, -1, :]
        
        non_white_top_idx = np.where(np.any(top < 255, axis=-1))[0]
        non_white_bottom_idx = np.where(np.any(bottom < 255, axis=-1))[0]
        non_white_left_idx = np.where(np.any(left < 255, axis=-1))[0]
        non_white_right_idx = np.where(np.any(right < 255, axis=-1))[0]
        
        print(f"  Top non-white count: {len(non_white_top_idx)} / {w}")
        if len(non_white_top_idx) > 0:
            print(f"    First 5 non-white top: indices={non_white_top_idx[:5]}, colors={[list(top[i]) for i in non_white_top_idx[:5]]}")
            
        print(f"  Bottom non-white count: {len(non_white_bottom_idx)} / {w}")
        if len(non_white_bottom_idx) > 0:
            print(f"    First 5 non-white bottom: indices={non_white_bottom_idx[:5]}, colors={[list(bottom[i]) for i in non_white_bottom_idx[:5]]}")
            
        print(f"  Left non-white count: {len(non_white_left_idx)} / {h}")
        if len(non_white_left_idx) > 0:
            print(f"    First 5 non-white left: indices={non_white_left_idx[:5]}, colors={[list(left[i]) for i in non_white_left_idx[:5]]}")
            
        print(f"  Right non-white count: {len(non_white_right_idx)} / {h}")
        if len(non_white_right_idx) > 0:
            print(f"    First 5 non-white right: indices={non_white_right_idx[:5]}, colors={[list(right[i]) for i in non_white_right_idx[:5]]}")
