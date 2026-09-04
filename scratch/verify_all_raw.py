import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2"

def clean_mask_contours(alpha_np):
    _, thresh = cv2.threshold(alpha_np, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return alpha_np
    largest_contour = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(alpha_np)
    cv2.drawContours(clean_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    return clean_mask

def main():
    print("Initializing rembg session...")
    session = new_session('u2net')
    
    if not os.path.exists(SRC_DIR):
        print(f"Source directory not found: {SRC_DIR}")
        return
        
    files = sorted([f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
    print(f"Found {len(files)} files to verify.")
    
    vertical_count = 0
    horizontal_count = 0
    empty_count = 0
    
    for idx, f in enumerate(files):
        path = os.path.join(SRC_DIR, f)
        img = Image.open(path)
        # Load raw pixels, no EXIF transpose
        img_rgba = remove(img, session=session)
        alpha = np.array(img_rgba.split()[3])
        mask = clean_mask_contours(alpha)
        
        ys, xs = np.where(mask > 0)
        if len(ys) == 0:
            print(f"[{idx+1}/100] {f}: Empty mask!")
            empty_count += 1
            continue
            
        y_min, y_max = ys.min(), ys.max()
        x_min, x_max = xs.min(), xs.max()
        
        h_box = y_max - y_min + 1
        w_box = x_max - x_min + 1
        
        # In the raw photo, the table is vertical.
        # The cowhide should be vertical too (even if wide, the planks are vertical).
        # Let's verify if the image aspect ratio is landscape (1616, 1080)
        # and if the bounding box is centered and vertical.
        # Since W_img = 1616, H_img = 1080:
        # A vertical hide will have height spanning most of H_img (e.g. 700-950 pixels).
        # Its width will be smaller than 1616 (e.g. 600-950 pixels).
        # So h_box is close to H_img.
        is_vertical_in_grid = h_box > (1080 * 0.5)
        
        if is_vertical_in_grid:
            vertical_count += 1
        else:
            horizontal_count += 1
            
        print(f"[{idx+1}/100] {f}: Raw Size={img.size}, BBox={w_box}x{h_box} -> Vertical Spine: {is_vertical_in_grid}")

    print("\nSummary:")
    print(f"  Vertical Spine: {vertical_count}")
    print(f"  Horizontal Spine: {horizontal_count}")
    print(f"  Empty Mask: {empty_count}")

if __name__ == "__main__":
    main()
