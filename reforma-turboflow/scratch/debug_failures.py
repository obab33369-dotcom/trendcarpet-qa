import os
import sys
import json
from PIL import Image, ImageDraw

sys.path.append(os.getcwd())

from vision_auto_corrector import (
    classify_and_size_product,
    CATEGORY_TARGETS,
    adjust_size_by_name,
    trim_bbox_to_pixels,
    calculate_scale,
    create_feathered_mask
)

# Paths
ARTIKLAR_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar"
BRAIN_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611"

def process_and_correct_debug(img_path, dest_path, bbox, category_info):
    category, target_w, target_h, floor_pct, is_centered = category_info
    
    with Image.open(img_path) as img:
        W, H = img.size
        
        # Expand bbox by 4% margin
        margin = 0.04
        ymin, xmin, ymax, xmax = bbox
        ymin_expanded = max(0.0, ymin - margin)
        xmin_expanded = max(0.0, xmin - margin)
        ymax_expanded = min(1.0, ymax + margin)
        xmax_expanded = min(1.0, xmax + margin)
        bbox_expanded = [ymin_expanded, xmin_expanded, ymax_expanded, xmax_expanded]
        
        trimmed_bbox = trim_bbox_to_pixels(img.convert('RGB'), bbox_expanded)
        
        ymin, xmin, ymax, xmax = trimmed_bbox
        w_curr = xmax - xmin
        h_curr = ymax - ymin
        cx_curr = (xmin + xmax) / 2
        cy_curr = (ymin + ymax) / 2
        
        scale = calculate_scale(category, w_curr, h_curr, target_w, target_h, floor_pct, is_centered)
        
        cx_target = 0.50
        if is_centered:
            cy_target = 0.50
        else:
            h_new_pct = h_curr * scale
            cy_target = (1.0 - floor_pct) - h_new_pct / 2
            
        # 2. Get product pixel bounds
        p_ymin_px = max(0, int(ymin * H))
        p_xmin_px = max(0, int(xmin * W))
        p_ymax_px = min(H, int(ymax * H))
        p_xmax_px = min(W, int(xmax * W))
        
        # 3. Sample initial background color from corners of original image to define scanning threshold
        corners_orig = [
            img.getpixel((15, 15)),
            img.getpixel((W - 15, 15)),
            img.getpixel((15, H - 15)),
            img.getpixel((W - 15, H - 15))
        ]
        r_orig = sum(c[0] for c in corners_orig) / 4.0
        g_orig = sum(c[1] for c in corners_orig) / 4.0
        b_orig = sum(c[2] for c in corners_orig) / 4.0
        bg_val_orig = 0.299 * r_orig + 0.587 * g_orig + 0.114 * b_orig
        bg_threshold = max(210.0, min(248.0, bg_val_orig - 8.0))
        
        # 4. Find crop bounding box (product + shadow) by scanning original image
        img_rgb = img.convert('RGB')
        pixels_orig = img_rgb.load()
        c_ymin_px, c_xmin_px = H, W
        c_ymax_px, c_xmax_px = 0, 0
        found_any = False
        
        for y in range(H):
            for x in range(W):
                r, g, b = pixels_orig[x, y]
                gray = 0.299 * r + 0.587 * g + 0.114 * b
                if gray <= bg_threshold:
                    found_any = True
                    if y < c_ymin_px: c_ymin_px = y
                    if y > c_ymax_px: c_ymax_px = y
                    if x < c_xmin_px: c_xmin_px = x
                    if x > c_xmax_px: c_xmax_px = x
                    
        if not found_any:
            c_ymin_px, c_xmin_px, c_ymax_px, c_xmax_px = p_ymin_px, p_xmin_px, p_ymax_px, p_xmax_px
        else:
            # Enforce that the crop box always covers the product bounding box to avoid cutting off light parts
            c_ymin_px = min(c_ymin_px, p_ymin_px)
            c_xmin_px = min(c_xmin_px, p_xmin_px)
            c_ymax_px = max(c_ymax_px, p_ymax_px)
            c_xmax_px = max(c_xmax_px, p_xmax_px)
            
            # Add 15 pixels padding for safety around the crop
            c_ymin_px = max(0, c_ymin_px - 15)
            c_xmin_px = max(0, c_xmin_px - 15)
            c_ymax_px = min(H, c_ymax_px + 15)
            c_xmax_px = min(W, c_xmax_px + 15)
            
        crop_w = c_xmax_px - c_xmin_px
        crop_h = c_ymax_px - c_ymin_px
        if crop_h <= 0: crop_h = 1
        if crop_w <= 0: crop_w = 1
        
        cropped_img = img.crop((c_xmin_px, c_ymin_px, c_xmax_px, c_ymax_px))
        
        # 5. Sample background color from the crop corners (lightest corner)
        crop_W, crop_H = cropped_img.size
        c1 = cropped_img.getpixel((5, 5))
        c2 = cropped_img.getpixel((crop_W - 5, 5))
        c3 = cropped_img.getpixel((5, crop_H - 5))
        c4 = cropped_img.getpixel((crop_W - 5, crop_H - 5))
        grays = [0.299*c[0] + 0.587*c[1] + 0.114*c[2] for c in [c1, c2, c3, c4]]
        best_idx = grays.index(max(grays))
        r_avg, g_avg, b_avg = [c1, c2, c3, c4][best_idx]
        bg_val = grays[best_idx]
        
        crop_pixels = cropped_img.load()
        
        # 6. Process crop pixels (desaturate & whiten surroundings)
        y1_crop = max(0, p_ymin_px - c_ymin_px)
        x1_crop = max(0, p_xmin_px - c_xmin_px)
        y2_crop = min(crop_h, p_ymax_px - c_ymin_px)
        x2_crop = min(crop_w, p_xmax_px - c_xmin_px)
        
        whitening_threshold = max(200.0, bg_val - 5.0)
        
        for y in range(crop_h):
            for x in range(crop_w):
                r, g, b = crop_pixels[x, y]
                
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                sat = (max_c - min_c) / max_c if max_c > 0 else 0.0
                gray = 0.299 * r + 0.587 * g + 0.114 * b
                
                in_bbox = (x1_crop <= x <= x2_crop) and (y1_crop <= y <= y2_crop)
                dist = ((r - r_avg)**2 + (g - g_avg)**2 + (b - b_avg)**2)**0.5
                
                is_furniture = False
                if in_bbox:
                    if (gray < 245) and (dist > 15):
                        if (sat >= 0.08) or (gray < 130):
                            is_furniture = True
                            
                if not is_furniture:
                    gray_new = min(255.0, gray * (255.0 / whitening_threshold))
                    val = int(gray_new)
                    crop_pixels[x, y] = (val, val, val)
                    
        # 7. Scale and paste onto a pure white canvas
        scaled_crop_w = max(1, int(crop_w * scale))
        scaled_crop_h = max(1, int(crop_h * scale))
        scaled_crop = cropped_img.resize((scaled_crop_w, scaled_crop_h), Image.Resampling.LANCZOS)
        
        mask = create_feathered_mask(scaled_crop.size, border=8)
        canvas = Image.new("RGB", (W, H), (255, 255, 255))
        
        # Calculate paste coordinates using product center and bottom leg alignment
        cx_in_crop = (p_xmin_px + p_xmax_px) / 2.0 - c_xmin_px
        cx_scaled = cx_in_crop * scale
        paste_x = int(cx_target * W - cx_scaled)
        
        if is_centered:
            cy_in_crop = (p_ymin_px + p_ymax_px) / 2.0 - c_ymin_px
            cy_scaled = cy_in_crop * scale
            paste_y = int(cy_target * H - cy_scaled)
        else:
            bottom_in_crop = p_ymax_px - c_ymin_px
            bottom_scaled = bottom_in_crop * scale
            paste_y = int((1.0 - floor_pct) * H - bottom_scaled)
            
        canvas.paste(scaled_crop, (paste_x, paste_y), mask)
        canvas.save(dest_path, "JPEG", quality=92)
        
    w_new = w_curr * scale
    h_new = h_curr * scale
    ymin_new = cy_target - h_new/2
    xmin_new = cx_target - w_new/2
    ymax_new = cy_target + h_new/2
    xmax_new = cx_target + w_new/2
    
    return {
        "scale_applied": scale,
        "shift_x": paste_x,
        "shift_y": paste_y,
        "new_bbox": [ymin_new, xmin_new, ymax_new, xmax_new],
        "new_width_pct": w_new,
        "new_height_pct": h_new
    }

def debug_sku(sku, name):
    print(f"\n--- Debugging SKU: {sku} ({name}) ---")
    img_name = f"{sku}.jpg"
    img_path = os.path.join(ARTIKLAR_DIR, img_name)
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        return
        
    category = classify_and_size_product(name)
    target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS[category]
    target_w, target_h = adjust_size_by_name(category, name, target_w, target_h)
    category_info = (category, target_w, target_h, floor_pct, is_centered)
    
    # Hand-coded predicted bboxes from first run to avoid repeating API calls
    bboxes = {
        "19011": [0.2855, 0.1852, 0.8845, 0.816],
        "2103": [0.607, 0.12, 0.842, 0.89],
        "2105": [0.29, 0.09, 0.88, 0.91]
    }
    bbox = bboxes.get(sku)
    print("Bbox used:", bbox)
    
    dest_path = os.path.join(BRAIN_DIR, f"debug_corrected_{sku}.jpg")
    meta = process_and_correct_debug(img_path, dest_path, bbox, category_info)
    print("Correction metadata:", json.dumps(meta, indent=2))
    print(f"Saved corrected debug image to {dest_path}")

if __name__ == '__main__':
    failures = [
        ("19011", "Soffbord 'Frida' - Natur/Svart"),
        ("2103", "TV-bänk 'Prime' - Valnöt/Mässing"),
        ("2105", "Skrivbord 'Prime' - Valnöt")
    ]
    for sku, name in failures:
        debug_sku(sku, name)
