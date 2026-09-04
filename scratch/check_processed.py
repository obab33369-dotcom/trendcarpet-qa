import os
import cv2
import numpy as np
from PIL import Image

PROCESSED_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Processed (1500x1500)"

def check_processed_file(filename):
    path = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
        
    img = Image.open(path)
    # Convert to grayscale
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    
    # Processed images have white background (255, 255, 255) and a dropshadow.
    # To isolate the cowhide, we threshold. Since the shadow is dark/gray, it might be included.
    # Let's use thresholding to find the cowhide. Let's find pixels that are not pure white (e.g. < 240)
    mask = (gray < 240).astype(np.uint8) * 255
    
    # Keep only largest contour to ignore dropshadow if it's separated (though it's attached)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"{filename}: No contours found!")
        return None
        
    largest_contour = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(gray)
    cv2.drawContours(clean_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    
    # Bounding box of the cowhide
    ys, xs = np.where(clean_mask > 0)
    if len(ys) == 0:
        return None
        
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    
    h_box = y_max - y_min + 1
    w_box = x_max - x_min + 1
    
    cropped = clean_mask[y_min:y_max+1, x_min:x_max+1]
    
    # Calculate top area vs bottom area
    mid_y = cropped.shape[0] // 2
    top_area = np.sum(cropped[:mid_y, :] > 0)
    bottom_area = np.sum(cropped[mid_y:, :] > 0)
    ratio_bt = bottom_area / top_area if top_area > 0 else 0
    
    return {
        "filename": filename,
        "w": w_box,
        "h": h_box,
        "ratio_bt": ratio_bt
    }

def main():
    if not os.path.exists(PROCESSED_DIR):
        print(f"Directory not found: {PROCESSED_DIR}")
        return
        
    files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
    print(f"Found {len(files)} processed files.")
    
    rump_up_count = 0
    rump_down_count = 0
    
    for f in files[:20]: # Check first 20
        res = check_processed_file(f)
        if res:
            if res['ratio_bt'] < 1.0:
                orient = "RUMP-UP (Wider at top)"
                rump_up_count += 1
            else:
                orient = "RUMP-DOWN (Wider at bottom)"
                rump_down_count += 1
            print(f"{res['filename']}: Ratio B/T={res['ratio_bt']:.3f} -> {orient}")
            
    print(f"\nSummary of first 20: RUMP-UP: {rump_up_count}, RUMP-DOWN: {rump_down_count}")

if __name__ == "__main__":
    main()
