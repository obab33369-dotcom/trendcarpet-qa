import os
from PIL import Image
import numpy as np

topaz_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\0615_stol-ystad-natur-svart-1-26U-wonder.webp"
orig_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Stol 'Ystad' - NaturSvart (19791)\artiklar\19791.jpg"

def analyze_borders(img_path, label):
    if not os.path.exists(img_path):
        print(f"{label} not found at {img_path}")
        return
    with Image.open(img_path) as img:
        img = img.convert('RGB')
        W, H = img.size
        img_np = np.array(img).astype(np.float32)
        print(f"\n--- Analyzing {label} ({W}x{H}) ---")
        
        # Check left 20 pixels
        left_slice = img_np[:, :20, :]
        left_mean = np.mean(left_slice, axis=(0,1))
        print(f"Left 20px mean color: R={left_mean[0]:.1f}, G={left_mean[1]:.1f}, B={left_mean[2]:.1f}")
        
        # Check right 20 pixels
        right_slice = img_np[:, -20:, :]
        right_mean = np.mean(right_slice, axis=(0,1))
        print(f"Right 20px mean color: R={right_mean[0]:.1f}, G={right_mean[1]:.1f}, B={right_mean[2]:.1f}")
        
        # Check bottom 20 pixels
        bottom_slice = img_np[-20:, :, :]
        bottom_mean = np.mean(bottom_slice, axis=(0,1))
        print(f"Bottom 20px mean color: R={bottom_mean[0]:.1f}, G={bottom_mean[1]:.1f}, B={bottom_mean[2]:.1f}")
        
        # Find if there are dark pixels on the left edge (x=0)
        left_edge = img_np[:, 0, :]
        left_edge_brightness = np.mean(left_edge, axis=1)
        dark_on_left = np.where(left_edge_brightness < 240)[0]
        if len(dark_on_left) > 0:
            print(f"Leftmost column (x=0) has {len(dark_on_left)} non-white pixels! (y range: {dark_on_left[0]} to {dark_on_left[-1]})")
            print(f"  Sample values: {left_edge[dark_on_left[0]:dark_on_left[0]+5]}")
        else:
            print("Leftmost column is purely white.")

        # Find if there are dark pixels on the bottom edge (y=H-1)
        bottom_edge = img_np[H-1, :, :]
        bottom_edge_brightness = np.mean(bottom_edge, axis=1)
        dark_on_bottom = np.where(bottom_edge_brightness < 240)[0]
        if len(dark_on_bottom) > 0:
            print(f"Bottommost row (y=H-1) has {len(dark_on_bottom)} non-white pixels! (x range: {dark_on_bottom[0]} to {dark_on_bottom[-1]})")
            print(f"  Sample values: {bottom_edge[dark_on_bottom[0]:dark_on_bottom[0]+5]}")
        else:
            print("Bottommost row is purely white.")

analyze_borders(topaz_path, "TEST TOPAZ Image")
analyze_borders(orig_path, "Original Image")
