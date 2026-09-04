import os
import json
import re
from PIL import Image

STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\review_test_20_only\review_status.json"
IMG_PATH = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images\artiklar\1400034.jpg"

def main():
    if not os.path.exists(STATUS_FILE):
        print("Status file not found")
        return
        
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = json.load(f)
        
    db_key = "artiklar/1400034.jpg"
    entry = status_db.get(db_key)
    if not entry:
        print(f"Key {db_key} not found in DB")
        return
        
    bbox = entry["original_bbox"]
    print("BBox from Gemini:", bbox)
    
    with Image.open(IMG_PATH) as img:
        W, H = img.size
        print(f"Image Size: {W}x{H}")
        
        ymin_gem = bbox[0] * H
        xmin_gem = bbox[1] * W
        ymax_gem = bbox[2] * H
        xmax_gem = bbox[3] * W
        
        print(f"Gemini BBox (Pixels): y:[{ymin_gem:.1f}, {ymax_gem:.1f}], x:[{xmin_gem:.1f}, {xmax_gem:.1f}]")
        
        # Let's see what body_w and body_h are
        body_w = xmax_gem - xmin_gem
        body_h = ymax_gem - ymin_gem
        print(f"Body: {body_w:.1f}x{body_h:.1f}")
        
        # Target sizes for stool
        target_size = 1000
        target_h = 0.54
        target_w = 0.54
        
        scale = (target_size * target_h) / body_h
        print(f"Initial height-based scale: {scale:.4f}")
        
        if body_w * scale > target_size * 0.90:
            new_scale = (target_size * 0.85) / body_w
            print(f"Width exceeds 90% (width*scale = {body_w * scale:.1f}). Clamping scale to: {new_scale:.4f}")
            scale = new_scale
            
        # Let's check margin_x scale limit
        cx_prod = (xmin_gem + xmax_gem) / 2.0
        margin_x = 0.04
        body_dist_left = max(1.0, cx_prod - xmin_gem)
        body_dist_right = max(1.0, xmax_gem - cx_prod)
        max_body_dist_x = max(body_dist_left, body_dist_right)
        
        scale_limit_x = (target_size * (0.5 - margin_x)) / max_body_dist_x
        print(f"Scale limit x (margins): {scale_limit_x:.4f} (max_body_dist_x = {max_body_dist_x:.1f})")
        
        final_scale = min(scale, scale_limit_x)
        print(f"Scale after limits: {final_scale:.4f}")
        
        # Height safety check
        floor_pct = 0.10
        floor_line = target_size - int(target_size * floor_pct)
        max_body_h_px = floor_line - target_size * 0.05
        max_body_h_px = max(max_body_h_px, target_size * 0.50)
        print(f"max_body_h_px: {max_body_h_px}")
        
        if body_h * final_scale > max_body_h_px:
            final_scale = max_body_h_px / body_h
            print(f"Exceeds height limit. Rescaling to: {final_scale:.4f}")
            
        print(f"Final calculated scale: {final_scale:.4f}")
        print(f"Scale in DB: {entry['correction_metadata']['scale_applied']:.4f}")

if __name__ == "__main__":
    main()
