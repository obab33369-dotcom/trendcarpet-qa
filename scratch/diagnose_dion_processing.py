import os
import sys
import json
import torch
import numpy as np
from PIL import Image

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
import vision_auto_corrector
from vision_auto_corrector import (
    classify_and_size_product, CATEGORY_TARGETS, trim_bbox_to_pixels, 
    call_gemini_vision, get_sam_predictor, get_sam3_text_prompt, calculate_scale
)

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\armchairs\Fåtölj _Dion_ - SammetRosa\Fåtölj _Dion_ - SammetRosa-03-W-wonder.jpg"

print("Querying Gemini Vision for source image bbox...")
category = "armchair"
prod_name = "Fåtölj Dion - SammetRosa"
bbox_src, is_closeup = call_gemini_vision(img_path, category, prod_name)
print("Gemini Bbox:", bbox_src, "is_closeup:", is_closeup)

with Image.open(img_path) as img:
    img = img.convert('RGB')
    W, H = img.size
    
    # Trim
    bbox_trimmed = trim_bbox_to_pixels(img, bbox_src)
    print("Trimmed Bbox:", bbox_trimmed)
    
    # SAM3 mask
    predictor = get_sam_predictor()
    text_prompts = get_sam3_text_prompt(category)
    print("Text prompts:", text_prompts)
    results = predictor(img_path, text=text_prompts)
    
    if len(results) > 0 and results[0].masks is not None:
        masks_tensor = results[0].masks.data
        combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy()
        print("Mask points sum:", np.sum(combined_mask))
    else:
        combined_mask = np.zeros((H, W), dtype=bool)
        print("No SAM3 mask found")
        
    # Check if there is shadow/background cast
    img_np = np.array(img).astype(np.float32)
    corners = [img_np[15, 15], img_np[15, W - 15], img_np[H - 15, 15], img_np[H - 15, W - 15]]
    r_avg = sum(float(c[0]) for c in corners) / 4.0
    g_avg = sum(float(c[1]) for c in corners) / 4.0
    b_avg = sum(float(c[2]) for c in corners) / 4.0
    bg_val = (r_avg + g_avg + b_avg) / 3.0
    
    ymin_src, xmin_src, ymax_src, xmax_src = bbox_trimmed
    ymin_margin = max(0.0, ymin_src - 0.12)
    xmin_margin = max(0.0, xmin_src - 0.12)
    ymax_margin = min(1.0, ymax_src + 0.25)
    xmax_margin = min(1.0, xmax_src + 0.12)
    
    y_norm = np.arange(H) / float(H)
    x_norm = np.arange(W) / float(W)
    y_grid = y_norm[:, np.newaxis]
    x_grid = x_norm[np.newaxis, :]
    
    in_bbox_mask = (y_grid >= ymin_margin) & (y_grid <= ymax_margin) & (x_grid >= xmin_margin) & (x_grid <= xmax_margin)
    shadow_zone = y_grid > (ymax_src - 0.08)
    
    dist_to_bg = np.sqrt(
        (img_np[:,:,0] - r_avg)**2 +
        (img_np[:,:,1] - g_avg)**2 +
        (img_np[:,:,2] - b_avg)**2
    )
    gray_ch = 0.299 * img_np[:,:,0] + 0.587 * img_np[:,:,1] + 0.114 * img_np[:,:,2]
    max_c = np.max(img_np, axis=-1)
    min_c = np.min(img_np, axis=-1)
    sat = np.where(max_c > 0, (max_c - min_c) / max_c, 0.0)
    
    is_furniture_heuristic = (gray_ch < 250) & (dist_to_bg > 5) & ((sat >= 0.02) | (gray_ch < 220))
    final_mask = combined_mask & in_bbox_mask & (is_furniture_heuristic | (~shadow_zone))
    
    p_ymin_px = max(0, int(ymin_src * H))
    p_xmin_px = max(0, int(xmin_src * W))
    p_ymax_px = min(H, int(ymax_src * H))
    p_xmax_px = min(W, int(xmax_src * W))
    
    p_ymin_px_actual = p_ymin_px
    p_xmin_px_actual = p_xmin_px
    p_ymax_px_actual = p_ymax_px
    p_xmax_px_actual = p_xmax_px
    
    mask_coords = np.argwhere(final_mask)
    if mask_coords.size > 0:
        m_ymin_px, m_xmin_px = mask_coords.min(axis=0)
        m_ymax_px, m_xmax_px = mask_coords.max(axis=0)
        print("Mask bounds:", m_ymin_px, m_xmin_px, m_ymax_px, m_xmax_px)
        if m_ymin_px < p_ymin_px: p_ymin_px_actual = m_ymin_px
        if m_xmin_px < p_xmin_px: p_xmin_px_actual = m_xmin_px
        if m_ymax_px > p_ymax_px: p_ymax_px_actual = m_ymax_px
        if m_xmax_px > p_xmax_px: p_xmax_px_actual = m_xmax_px
        
    print("Actual bounding pixels (bbox + mask union):")
    print("ymin:", p_ymin_px_actual, "xmin:", p_xmin_px_actual, "ymax:", p_ymax_px_actual, "xmax:", p_xmax_px_actual)
    
    # Let's save a visualization to verify
    img_draw = img.copy()
    draw = ImageDraw.Draw(img_draw)
    # draw bbox_src in red
    draw.rectangle([xmin_src*W, ymin_src*H, xmax_src*W, ymax_src*H], outline="red", width=5)
    # draw actual in green
    draw.rectangle([p_xmin_px_actual, p_ymin_px_actual, p_xmax_px_actual, p_ymax_px_actual], outline="green", width=3)
    img_draw.save(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\diagnose_dion_vis.jpg")
    print("Saved vis to artifacts.")
