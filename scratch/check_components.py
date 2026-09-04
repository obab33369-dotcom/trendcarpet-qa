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

def analyze_segments(filename, session):
    path = os.path.join(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2", filename)
    img = Image.open(path)
    img_rgba = remove(img, session=session)
    alpha = np.array(img_rgba.split()[3])
    mask = clean_mask_contours(alpha)
    
    ys, xs = np.where(mask > 0)
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    
    h = y_max - y_min + 1
    w_box = x_max - x_min + 1
    
    # We will print the segment stats for rows at 5% increments
    print(f"\n{filename} (h={h}, w={w_box}):")
    
    for i in range(20):
        pct = i * 5
        y = y_min + int(i * 0.05 * h)
        row = (mask[y, x_min:x_max+1] > 0).astype(int)
        
        # Count segments
        # Pad row to detect segments at edges
        padded = np.concatenate(([0], row, [0]))
        diff = np.diff(padded)
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        
        num_segments = len(starts)
        
        gaps = []
        if num_segments > 1:
            for j in range(num_segments - 1):
                gap_size = starts[j+1] - ends[j]
                gaps.append(gap_size)
                
        gap_str = f", gaps={gaps}" if gaps else ""
        print(f"  {pct}% (y={y}): segments={num_segments}{gap_str}")

if __name__ == "__main__":
    session = new_session('u2net')
    for f in ["AGJM5060.JPG", "CSKG8106.JPG", "AMXR5849.JPG", "BPQA5442.JPG"]:
        analyze_segments(f, session)
