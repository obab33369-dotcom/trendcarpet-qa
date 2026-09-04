import sys
import os
import json
from PIL import Image

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
import vision_auto_corrector

artiklar_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected\artiklar"
img_name = "19791.jpg"
img_path = os.path.join(artiklar_dir, img_name)

sku = "19791"
prod_name = "Stol 'Ystad' - NaturSvart"

print("--- DEBUGGING 19791.jpg PROCESS ---")
print(f"Reviewed Image Path: {img_path}")
print(f"Exists: {os.path.exists(img_path)}")

# Load original status db to get category
status_db_path = os.path.join(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected", "review_status.json")
with open(status_db_path, 'r', encoding='utf-8') as f:
    status_db = json.load(f)

db_key = f"artiklar/{img_name}"
entry = status_db.get(db_key, {})
category = entry.get("category", "chair_dining")
print(f"Category: {category}")

# Call get_sam_predictor to initialize it
predictor = vision_auto_corrector.get_sam_predictor()

# Run find_original_source_image
src_image = vision_auto_corrector.find_original_source_image(sku, prod_name, slot=1)
print(f"Matched source image: {src_image}")

# Open source image and check bounds
with Image.open(src_image) as img:
    W, H = img.size
    print(f"Source size WxH: {W}x{H}")

# Run call_gemini_vision on source image
print("Querying Gemini Vision on source image...")
bbox_src, is_closeup = vision_auto_corrector.call_gemini_vision(src_image, category, prod_name)
print(f"Gemini source bbox: {bbox_src}, is_closeup: {is_closeup}")

# Run trim_bbox_to_pixels
with Image.open(src_image) as img:
    bbox_trimmed = vision_auto_corrector.trim_bbox_to_pixels(img, bbox_src)
print(f"Trimmed source bbox: {bbox_trimmed}")

# Get SAM3 mask
text_prompts = vision_auto_corrector.get_sam3_text_prompt(category)
results = predictor(src_image, text=text_prompts)
import torch
import numpy as np
if len(results) > 0 and results[0].masks is not None:
    masks_tensor = results[0].masks.data
    combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy()
else:
    combined_mask = np.zeros((H, W), dtype=bool)

# Let's inspect final mask boundaries
ymin_src, xmin_src, ymax_src, xmax_src = bbox_trimmed
ymin_margin = max(0.0, ymin_src - 0.12)
xmin_margin = max(0.0, xmin_src - 0.05)
ymax_margin = min(1.0, ymax_src + 0.25)
xmax_margin = min(1.0, xmax_src + 0.05)

y_norm = np.arange(H) / float(H)
x_norm = np.arange(W) / float(W)
y_grid = y_norm[:, np.newaxis]
x_grid = x_norm[np.newaxis, :]

in_bbox_mask = (y_grid >= ymin_margin) & (y_grid <= ymax_margin) & (x_grid >= xmin_margin) & (x_grid <= xmax_margin)
shadow_zone = y_grid > (ymax_src - 0.08)

# Sample background color
img_np = np.array(Image.open(src_image).convert('RGB')).astype(np.float32)
corners = [img_np[15, 15], img_np[15, W - 15], img_np[H - 15, 15], img_np[H - 15, W - 15]]
r_avg = sum(float(c[0]) for c in corners) / 4.0
g_avg = sum(float(c[1]) for c in corners) / 4.0
b_avg = sum(float(c[2]) for c in corners) / 4.0
bg_val = (r_avg + g_avg + b_avg) / 3.0

dist_to_bg = np.sqrt((img_np[:,:,0]-r_avg)**2 + (img_np[:,:,1]-g_avg)**2 + (img_np[:,:,2]-b_avg)**2)
gray_ch = 0.299 * img_np[:,:,0] + 0.587 * img_np[:,:,1] + 0.114 * img_np[:,:,2]
max_c = np.max(img_np, axis=-1)
min_c = np.min(img_np, axis=-1)
sat = np.where(max_c > 0, (max_c - min_c) / max_c, 0.0)

is_furniture_shadow = (gray_ch < 250) & (dist_to_bg > 5) & ((sat >= 0.03) | (gray_ch < 130))
final_mask = combined_mask & in_bbox_mask & (is_furniture_shadow | (~shadow_zone))

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
    print(f"SAM3 Mask min/max coords: y=[{m_ymin_px}, {m_ymax_px}], x=[{m_xmin_px}, {m_xmax_px}]")
    if m_ymin_px < p_ymin_px: p_ymin_px_actual = m_ymin_px
    if m_xmin_px < p_xmin_px: p_xmin_px_actual = m_xmin_px
    if m_ymax_px > p_ymax_px: p_ymax_px_actual = m_ymax_px
    if m_xmax_px > p_xmax_px: p_xmax_px_actual = m_xmax_px

floor_standing_categories = ["sofa_2_seat", "sofa_3_seat", "bench_hallway", "table_dining", "table_coffee", "desk", "sideboard_credenza", "chair_dining", "armchair", "barstool", "stool", "lamp_floor"]
if category in floor_standing_categories:
    detected_ymax_pct = p_ymax_px_actual / float(H)
    print(f"Detected ymax pct: {detected_ymax_pct:.4f}")
    if detected_ymax_pct > 0.88:
        print("Floor heuristic triggered: extending actual bottom to H")
        p_ymax_px_actual = H

print(f"Actual bounds in pixels: y=[{p_ymin_px_actual}, {p_ymax_px_actual}], x=[{p_xmin_px_actual}, {p_xmax_px_actual}]")
w_curr = (p_xmax_px_actual - p_xmin_px_actual) / float(W)
h_curr = (p_ymax_px_actual - p_ymin_px_actual) / float(H)
print(f"w_curr={w_curr:.4f}, h_curr={h_curr:.4f}")

# Target info
target_w, target_h, floor_pct, is_centered = vision_auto_corrector.CATEGORY_TARGETS[category]
target_w, target_h = vision_auto_corrector.adjust_size_by_name(category, prod_name, target_w, target_h)
print(f"Target size: w={target_w}, h={target_h}, floor_pct={floor_pct}, is_centered={is_centered}")

W_out, H_out = 1000, 1000
scale = vision_auto_corrector.calculate_scale(category, w_curr, h_curr, target_w, target_h, floor_pct, is_centered, W, H, W_out, H_out)
print(f"Calculated scale: {scale:.6f}")

# Paste calculation
body_cx_scaled = ((p_xmin_px_actual + p_xmax_px_actual) / 2.0) * scale
body_cy_scaled = ((p_ymin_px_actual + p_ymax_px_actual) / 2.0) * scale
body_bottom_scaled = p_ymax_px_actual * scale

paste_x = int((W_out / 2.0) - body_cx_scaled)
floor_y = int(H_out * (1.0 - floor_pct))
paste_y = floor_y - int(body_bottom_scaled)
print(f"Paste coordinates: x={paste_x}, y={paste_y}")

# Check if pasting the resized image will clip the shadow!
# The resized image has size: W_new, H_new
W_new = int(W * scale)
H_new = int(H * scale)
print(f"New scaled size: {W_new}x{H_new}")
print(f"Paste range: x=[{paste_x}, {paste_x + W_new}], y=[{paste_y}, {paste_y + H_new}]")

# Check if the shadow zone is clipped at the left edge of the source image!
# Let's check if there are non-white pixels near x=0 in the source image itself!
# We can sample the left-most column of the source image near the bottom.
img_pil = Image.open(src_image).convert('RGB')
left_col = [img_pil.getpixel((0, y)) for y in range(int(H*0.7), H)]
min_left_col = min(sum(c)/3.0 for c in left_col)
print(f"Minimum brightness in left-most column of source image (y=70% to 100%): {min_left_col:.1f}")
if min_left_col < 240:
    print("WARNING: The left-most column of the source image itself contains non-white pixels! The shadow is ALREADY cut in the source image!")

# Check if the right-most column contains non-white pixels
right_col = [img_pil.getpixel((W-1, y)) for y in range(int(H*0.7), H)]
min_right_col = min(sum(c)/3.0 for c in right_col)
print(f"Minimum brightness in right-most column of source image (y=70% to 100%): {min_right_col:.1f}")

# Check if the bottom-most row contains non-white pixels
bottom_row = [img_pil.getpixel((x, H-1)) for x in range(W)]
min_bottom_row = min(sum(c)/3.0 for c in bottom_row)
print(f"Minimum brightness in bottom-most row of source image: {min_bottom_row:.1f}")
