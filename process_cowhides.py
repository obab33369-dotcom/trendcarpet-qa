import os
import sys
import shutil
import cv2
from PIL import Image, ImageFilter, ImageOps
from rembg import remove, new_session
from transparent_background import Remover
import numpy as np

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2"
PARENT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10"

BACKUP_DIR = os.path.join(PARENT_DIR, "Batch 2 - Originals Backup")
OUT_ORIG_DIR = os.path.join(PARENT_DIR, "Batch 2 - Processed (Original Size)")
OUT_1500_DIR = os.path.join(PARENT_DIR, "Batch 2 - Processed (1500x1500)")

# Naming suffix
NAME_SUFFIX = "-Kohud-Kuhfell-Cowhide-Kuskinn"


def clean_mask_hybrid(inspyrenet_mask, u2net_alpha):
    """
    Hybrid mask: union of InSPyReNet + u2net, then keep largest contour filled.
    InSPyReNet preserves white fur better, u2net provides reliable dark-fur coverage.
    The union ensures we get the best of both.
    """
    # Convert InSPyReNet mask to grayscale if needed
    if len(inspyrenet_mask.shape) == 3:
        inspyrenet_mask = cv2.cvtColor(inspyrenet_mask, cv2.COLOR_BGR2GRAY)

    # Threshold both
    _, mask_isp = cv2.threshold(inspyrenet_mask, 30, 255, cv2.THRESH_BINARY)
    _, mask_u2 = cv2.threshold(u2net_alpha, 30, 255, cv2.THRESH_BINARY)

    # Union of both masks
    combined = cv2.bitwise_or(mask_isp, mask_u2)

    # Morphological closing to fill small gaps between the two masks
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

    # Keep only the largest contour, filled solid
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return combined

    largest = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(combined)
    cv2.drawContours(clean_mask, [largest], -1, 255, thickness=cv2.FILLED)

    # Smooth edges
    clean_mask = cv2.GaussianBlur(clean_mask, (3, 3), 0)
    return clean_mask


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


def process_single_pipeline(img_path, filename, inspyrenet_remover, u2net_session):
    img = Image.open(img_path)
    img = ImageOps.exif_transpose(img)
    orig_w, orig_h = img.size

    # 1. Dual segmentation
    print(f"  1. Segmenting (InSPyReNet + u2net hybrid)...")
    isp_result = inspyrenet_remover.process(img, type='map')
    isp_mask = np.array(isp_result)

    u2_rgba = remove(img, session=u2net_session)
    u2_alpha = np.array(u2_rgba.split()[3])

    # 2. Hybrid mask
    print(f"  2. Building hybrid mask...")
    clean_alpha = clean_mask_hybrid(isp_mask, u2_alpha)

    # Merge clean alpha with original RGB
    img_rgba_cleaned = Image.merge(
        "RGBA",
        (img.split()[0], img.split()[1], img.split()[2], Image.fromarray(clean_alpha))
    )

    # 3. Detect orientation geometrically
    print(f"  3. Detecting orientation...")
    rump_dir = detect_rump_direction_geometric(clean_alpha)
    rotation_map = {'bottom': 0, 'top': 180, 'left': 270, 'right': 90}
    rotation = rotation_map.get(rump_dir, 0)
    print(f"     Rump: '{rump_dir}' -> rotate {rotation}°")

    if rotation != 0:
        img_rgba_cleaned = img_rgba_cleaned.rotate(-rotation, expand=True)

    # 4. Crop to bounding box
    bbox = img_rgba_cleaned.getbbox()
    if not bbox:
        bbox = (0, 0, img_rgba_cleaned.width, img_rgba_cleaned.height)
    cropped_cowhide = img_rgba_cleaned.crop(bbox)

    # 5. Sharpen
    print(f"  4. Sharpening + compositing...")
    sharpened = cropped_cowhide.filter(
        ImageFilter.UnsharpMask(radius=2.0, percent=180, threshold=1)
    )

    # 6. Composite
    composited_1500 = composite_with_shadow(sharpened, 1500)
    max_orig_dim = max(orig_w, orig_h)
    composited_orig = composite_with_shadow(sharpened, max_orig_dim)

    return composited_orig, composited_1500, max_orig_dim


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


def main():
    print("Starting Cowhide Pipeline (InSPyReNet + u2net hybrid)...")
    print("=" * 60)

    if not os.path.exists(SRC_DIR):
        print(f"[Error] Source directory does not exist: {SRC_DIR}")
        sys.exit(1)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(OUT_ORIG_DIR, exist_ok=True)
    os.makedirs(OUT_1500_DIR, exist_ok=True)

    images = sorted([f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
    print(f"Found {len(images)} images to process.")

    # Backup
    for f in images:
        bak = os.path.join(BACKUP_DIR, f)
        if not os.path.exists(bak):
            shutil.copy2(os.path.join(SRC_DIR, f), bak)

    # Load models once
    print("Loading InSPyReNet model...")
    inspyrenet_remover = Remover()
    print("Loading u2net model...")
    u2net_session = new_session('u2net')
    print("Models loaded!\n")

    processed_count = 0

    for idx, f in enumerate(images):
        base_name = os.path.splitext(f)[0]
        out_filename = f"{base_name}{NAME_SUFFIX}.jpg"
        out_orig_path = os.path.join(OUT_ORIG_DIR, out_filename)
        out_1500_path = os.path.join(OUT_1500_DIR, out_filename)

        print(f"\nProcessing [{idx+1}/{len(images)}]: {f}")
        src_path = os.path.join(SRC_DIR, f)

        try:
            composited_orig, composited_1500, max_dim = process_single_pipeline(
                src_path, f, inspyrenet_remover, u2net_session
            )

            composited_orig.save(out_orig_path, "JPEG", quality=90)
            composited_1500.save(out_1500_path, "JPEG", quality=90)
            print(f"  Saved: {max_dim}x{max_dim} + 1500x1500")
            processed_count += 1

        except Exception as e:
            print(f"[ERROR] {f}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Pipeline finished! {processed_count}/{len(images)} processed.")


if __name__ == "__main__":
    main()
