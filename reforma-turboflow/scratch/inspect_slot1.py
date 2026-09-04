import os
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reforma_pipeline.qa_checker import QAChecker

checker = QAChecker()

# Path to the generated zoom slot 1 image
img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\WS-8651A-BlackBlack-NEW_1.jpg"

if os.path.exists(img_path):
    with Image.open(img_path) as img:
        print("Image format:", img.format, "size:", img.size)
        # Bounding box coordinates from DB: WS-8651A-BlackBlack-NEW_1_468550_1780569156 : [634, 648, 1337, 1691]
        bbox_clean = [634, 648, 1337, 1691]
        
        # Let's run run_diagnostics.
        # But wait! We need to know crop_box, paste_pos, and scale used during composition.
        # We can run the heuristics directly on the canvas image to see what pixels are non-white.
        # Let's read the image array
        arr = np.array(img.convert('RGB'))
        w, h = img.size
        
        # Background Purity Check
        top_edge = arr[0:10, :, :]
        left_edge = arr[:, 0:10, :]
        right_edge = arr[:, -10:, :]
        edges = [top_edge.reshape(-1, 3), left_edge.reshape(-1, 3), right_edge.reshape(-1, 3)]
        bg_pixels = np.concatenate(edges, axis=0)
        non_white_bg_count = np.sum(np.any(bg_pixels < 250, axis=-1))
        print("Non-white bg count:", non_white_bg_count)
        
        # Let's find all non-white pixels in the image to see where the product actually sits!
        diff_from_white = np.sum(255 - arr, axis=-1)
        non_white_mask = diff_from_white > 15
        
        # Ignore 5px thin border
        non_white_mask[:, :5] = False
        non_white_mask[:, -5:] = False
        
        coords = np.argwhere(non_white_mask)
        if coords.size > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            print(f"Product bounding box in composed canvas: x_min={x_min}, x_max={x_max}, y_min={y_min}, y_max={y_max}")
            mid_x = (x_min + x_max) / 2
            centering_error = mid_x - 1000
            print(f"Centering error: {centering_error}px (mid_x={mid_x:.1f})")
            
            # Let's see the vertical mass centering
            # The seat Y range for chairs is 50%-65% of the body height.
            body_h = y_max - y_min
            y_start = y_min + int(0.50 * body_h)
            y_end = y_min + int(0.65 * body_h)
            upper_mass = arr[y_start:y_end, :, :]
            diff_from_white_um = np.sum(255 - upper_mass, axis=-1)
            non_white_mask_um = diff_from_white_um > 15
            non_white_mask_um[:, :5] = False
            non_white_mask_um[:, -5:] = False
            coords_um = np.argwhere(non_white_mask_um)
            if coords_um.size > 0:
                x_min_um = coords_um[:, 1].min()
                x_max_um = coords_um[:, 1].max()
                mid_x_um = (x_min_um + x_max_um) / 2
                centering_error_um = mid_x_um - 1000
                print(f"Upper mass (50%-65% height) box: x_min={x_min_um}, x_max={x_max_um}, mid_x={mid_x_um:.1f}")
                print(f"Upper mass centering error: {centering_error_um}px")
        else:
            print("No non-white pixels found!")
else:
    print("File not found:", img_path)
