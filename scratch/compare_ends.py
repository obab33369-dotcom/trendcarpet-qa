import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def clean_mask_contours(alpha_np):
    _, thresh = cv2.threshold(alpha_np, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return alpha_np
    largest_contour = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(alpha_np)
    cv2.drawContours(clean_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    return clean_mask

def analyze_cleft_depth(filename, session):
    path = os.path.join(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2", filename)
    img = Image.open(path)
    img_rgba = remove(img, session=session)
    alpha = np.array(img_rgba.split()[3])
    mask = clean_mask_contours(alpha)
    
    ys, xs = np.where(mask > 0)
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    
    x_mid = (x_min + x_max) // 2
    h = y_max - y_min + 1
    w_box = x_max - x_min + 1
    
    # Define a window around center to be robust to off-center spine
    window = max(2, int(w_box * 0.03))
    
    # For each row y, check if the center is "empty"
    # We define it as empty if the average mask value in the center window is < 0.1 (10%)
    center_empty = []
    for y in range(y_min, y_max + 1):
        center_val = np.mean(mask[y, x_mid - window : x_mid + window + 1]) / 255.0
        center_empty.append(center_val < 0.2)
        
    # Calculate top cleft depth: number of consecutive empty rows from y_min
    top_cleft = 0
    for val in center_empty:
        if val:
            top_cleft += 1
        else:
            break
            
    # Calculate bottom cleft depth: number of consecutive empty rows from y_max going upwards
    bottom_cleft = 0
    for val in reversed(center_empty):
        if val:
            bottom_cleft += 1
        else:
            break
            
    print(f"\n{filename} (h={h}):")
    print(f"  Top empty depth = {top_cleft} rows ({top_cleft/h*100:.1f}%)")
    print(f"  Bottom empty depth = {bottom_cleft} rows ({bottom_cleft/h*100:.1f}%)")

if __name__ == "__main__":
    session = new_session('u2net')
    for f in ["AGJM5060.JPG", "CSKG8106.JPG", "AMXR5849.JPG", "BPQA5442.JPG"]:
        analyze_cleft_depth(f, session)
