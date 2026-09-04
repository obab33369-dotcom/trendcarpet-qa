import os
import sys
import shutil
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps

# Paths
EXTRACTED_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cut_out_cowhide"
PARENT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10"

OUT_ORIG_DIR = os.path.join(PARENT_DIR, "Batch 2 - Processed (Original Size)")
OUT_1500_DIR = os.path.join(PARENT_DIR, "Batch 2 - Processed (1500x1500)")

NAME_SUFFIX = "-Kohud-Kuhfell-Cowhide-Kuskinn"

# Create directories if they do not exist
os.makedirs(OUT_ORIG_DIR, exist_ok=True)
os.makedirs(OUT_1500_DIR, exist_ok=True)

# Delete existing processed files in the directory to clean up
for d in [OUT_ORIG_DIR, OUT_1500_DIR]:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(NAME_SUFFIX + ".jpg"):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass

def detect_rump_direction_geometric(mask):
    """
    Purely geometric rump detection. Measures the maximum span in the outer 20%
    of each side. The side with the widest span is the rump.
    """
    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return 'bottom'

    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    H = y_max - y_min + 1
    W = x_max - x_min + 1

    cropped = mask[y_min:y_max + 1, x_min:x_max + 1]
    slice_pct = 0.20

    # Horizontal spans in top and bottom slices
    slice_h = max(1, int(H * slice_pct))

    top_spans = []
    for r in range(slice_h):
        row_pixels = np.where(cropped[r, :] > 0)[0]
        if len(row_pixels) > 0:
            top_spans.append(row_pixels.max() - row_pixels.min() + 1)
    max_span_top = max(top_spans) if top_spans else 0

    bottom_spans = []
    for r in range(H - slice_h, H):
        row_pixels = np.where(cropped[r, :] > 0)[0]
        if len(row_pixels) > 0:
            bottom_spans.append(row_pixels.max() - row_pixels.min() + 1)
    max_span_bottom = max(bottom_spans) if bottom_spans else 0

    # Vertical spans in left and right slices
    slice_w = max(1, int(W * slice_pct))

    left_spans = []
    for c in range(slice_w):
        col_pixels = np.where(cropped[:, c] > 0)[0]
        if len(col_pixels) > 0:
            left_spans.append(col_pixels.max() - col_pixels.min() + 1)
    max_span_left = max(left_spans) if left_spans else 0

    right_spans = []
    for c in range(W - slice_w, W):
        col_pixels = np.where(cropped[:, c] > 0)[0]
        if len(col_pixels) > 0:
            right_spans.append(col_pixels.max() - col_pixels.min() + 1)
    max_span_right = max(right_spans) if right_spans else 0

    is_vertical = H > W
    if is_vertical:
        return 'top' if max_span_top > max_span_bottom else 'bottom'
    else:
        return 'left' if max_span_left > max_span_right else 'right'

def composite_with_shadow(cropped_cowhide, target_size, padding_pct=0.08):
    S = target_size
    max_fit_size = int(S * (1 - 2 * padding_pct))

    w_crop, h_crop = cropped_cowhide.size
    scale = min(max_fit_size / w_crop, max_fit_size / h_crop)
    new_w = int(w_crop * scale)
    new_h = int(h_crop * scale)

    resized = cropped_cowhide.resize((new_w, new_h), Image.Resampling.LANCZOS)

    scale_factor = S / 1500.0
    dx = int(-12 * scale_factor)
    dy = int(12 * scale_factor)
    blur_radius = max(3, int(6 * scale_factor))
    shadow_opacity = 0.18

    alpha = resized.split()[3]
    shadow_mask = Image.eval(alpha, lambda a: int(a * shadow_opacity))

    canvas = Image.new('RGBA', (S, S), (255, 255, 255, 255))
    x_pos = (S - new_w) // 2
    y_pos = (S - new_h) // 2

    shadow_canvas = Image.new('L', (S, S), 0)
    shadow_canvas.paste(shadow_mask, (x_pos + dx, y_pos + dy), mask=alpha)
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(blur_radius))

    shadow_rgba = Image.new('RGBA', (S, S), (0, 0, 0, 255))
    canvas.paste(shadow_rgba, (0, 0), mask=shadow_canvas)
    canvas.paste(resized, (x_pos, y_pos), mask=resized)
    return canvas.convert('RGB')

def process_file(img_path, filename):
    img = Image.open(img_path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
        
    orig_w, orig_h = img.size
    
    # Extract alpha mask
    alpha = np.array(img.split()[3])
    
    # Threshold mask to binary
    _, mask = cv2.threshold(alpha, 30, 255, cv2.THRESH_BINARY)
    
    # Detect orientation
    rump_dir = detect_rump_direction_geometric(mask)
    rotation_map = {'bottom': 0, 'top': 180, 'left': 270, 'right': 90}
    rotation = rotation_map.get(rump_dir, 0)
    
    img_rgba = img
    if rotation != 0:
        img_rgba = img_rgba.rotate(-rotation, expand=True)
        # Recalculate alpha mask for cropped bounding box after rotation
        alpha_rot = np.array(img_rgba.split()[3])
        _, mask = cv2.threshold(alpha_rot, 30, 255, cv2.THRESH_BINARY)
        
    # Crop to bounding box
    bbox = img_rgba.getbbox()
    if not bbox:
        bbox = (0, 0, img_rgba.width, img_rgba.height)
    cropped_cowhide = img_rgba.crop(bbox)
    
    # Sharpen
    sharpened = cropped_cowhide.filter(
        ImageFilter.UnsharpMask(radius=2.0, percent=180, threshold=1)
    )
    
    # Composite
    composited_1500 = composite_with_shadow(sharpened, 1500)
    max_orig_dim = max(orig_w, orig_h)
    composited_orig = composite_with_shadow(sharpened, max_orig_dim)
    
    return composited_orig, composited_1500, max_orig_dim, rump_dir, rotation

def main():
    files = sorted([f for f in os.listdir(EXTRACTED_DIR) if f.lower().endswith('.png')])
    print(f"Found {len(files)} cut out PNG files to process.")
    
    processed_count = 0
    for idx, f in enumerate(files):
        base_name = os.path.splitext(f)[0]
        out_filename = f"{base_name}{NAME_SUFFIX}.jpg"
        out_orig_path = os.path.join(OUT_ORIG_DIR, out_filename)
        out_1500_path = os.path.join(OUT_1500_DIR, out_filename)
        
        src_path = os.path.join(EXTRACTED_DIR, f)
        print(f"[{idx+1}/{len(files)}] Processing: {f}...", end=" ")
        
        try:
            comp_orig, comp_1500, max_dim, rump_dir, rot = process_file(src_path, f)
            
            comp_orig.save(out_orig_path, "JPEG", quality=92)
            comp_1500.save(out_1500_path, "JPEG", quality=92)
            print(f"Success! Rump: {rump_dir} (rotated {rot} deg). Saved {max_dim}x{max_dim} and 1500x1500px.")
            processed_count += 1
        except Exception as e:
            print(f"ERROR: {e}")
            
    print(f"\nProcessing finished! {processed_count}/{len(files)} files successfully processed.")
    print(f"Outputs saved to:\n  Originals: {OUT_ORIG_DIR}\n  1500x1500px: {OUT_1500_DIR}")

if __name__ == "__main__":
    main()
