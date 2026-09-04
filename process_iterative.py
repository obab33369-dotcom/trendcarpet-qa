"""
Iterative cowhide processing pipeline with Gemini quality verification.

Round 1: InSPyReNet + u2net hybrid (best for white fur)
Round 2: u2net only (tighter mask, less table inclusion) for rejects
Round 3: InSPyReNet only for remaining rejects
Round 4: birefnet for any still remaining

Each round: process -> Gemini verifies -> approved to output, rejected to next round.
"""
import os
import sys
import json
import time
import base64
import cv2
import shutil
import numpy as np
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps
from rembg import remove, new_session
from transparent_background import Remover
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2"
PARENT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10"
APPROVED_ORIG_DIR = os.path.join(PARENT_DIR, "Batch 2 - Approved (Original Size)")
APPROVED_1500_DIR = os.path.join(PARENT_DIR, "Batch 2 - Approved (1500x1500)")
NAME_SUFFIX = "-Kohud-Kuhfell-Cowhide-Kuskinn"

os.makedirs(APPROVED_ORIG_DIR, exist_ok=True)
os.makedirs(APPROVED_1500_DIR, exist_ok=True)

# Load Gemini API Key
def load_gemini_key():
    env_path = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

GEMINI_API_KEY = load_gemini_key()
if not GEMINI_API_KEY:
    print("[ERROR] Gemini API key not found in GEMINI_API_KEY.env!")
    sys.exit(1)

VERIFY_PROMPT = """You are a quality control inspector for cowhide product photos.

Examine this processed cowhide image and check for these issues:

1. **Background contamination**: Is there any visible table, floor, wood board, numbers/labels, 
   or other non-cowhide objects? The background should be PURE WHITE only.
2. **Orientation**: The rump (widest part) should be at the BOTTOM. The neck/head (narrower) 
   should be at the TOP. The legs should point outward.
3. **Completeness**: Is the cowhide silhouette complete? No large chunks should be cut off.
   White fur areas should be preserved, not removed.

Respond with EXACTLY this JSON format:
{
  "approved": true,
  "issues": [],
  "confidence": 0.95
}
Where approved is true/false, and issues is a list of specific issues found (or empty if approved).

Be strict about background contamination - ANY visible table/floor/labels = reject.
Be lenient about minor edge imperfections - small fuzzy edges are OK.
"""


def verify_with_gemini(img_path, max_retries=3):
    """Send processed image to Gemini for quality verification."""
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((600, 600))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"    Error preparing image for Gemini: {e}")
        return {"approved": False, "issues": [f"Image preparation error: {str(e)}"], "confidence": 0}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    data = {
        "contents": [
            {
                "parts": [
                    {"text": VERIFY_PROMPT},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                resp_json = res.json()
                text = resp_json['candidates'][0]['content']['parts'][0]['text']
                result = json.loads(text.strip())
                return result
            elif res.status_code == 429:
                backoff = 6 * (attempt + 1)
                print(f"    Rate limit hit, waiting {backoff} seconds...")
                time.sleep(backoff)
            else:
                print(f"    API Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"    Attempt {attempt+1} failed: {e}")
        time.sleep(2)
        
    return {"approved": False, "issues": ["Gemini API error / timeout"], "confidence": 0}


# ========== MASK STRATEGIES ==========

def clean_mask_largest(mask_np, threshold=30):
    """Keep only the largest contour, filled solid."""
    if len(mask_np.shape) == 3:
        mask_np = cv2.cvtColor(mask_np, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(mask_np, threshold, 255, cv2.THRESH_BINARY)
    cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return mask_np
    largest = max(cs, key=cv2.contourArea)
    m = np.zeros(mask_np.shape[:2], dtype=np.uint8)
    cv2.drawContours(m, [largest], -1, 255, cv2.FILLED)
    m = cv2.GaussianBlur(m, (3, 3), 0)
    return m


def strategy_hybrid(img_pil, inspyrenet_remover, u2net_session):
    """Round 1: InSPyReNet + u2net union (best for white fur)."""
    isp_result = inspyrenet_remover.process(img_pil, type='map')
    isp_mask = np.array(isp_result)
    if len(isp_mask.shape) == 3:
        isp_mask = cv2.cvtColor(isp_mask, cv2.COLOR_BGR2GRAY)

    u2_rgba = remove(img_pil, session=u2net_session)
    u2_alpha = np.array(u2_rgba.split()[3])

    _, m1 = cv2.threshold(isp_mask, 30, 255, cv2.THRESH_BINARY)
    _, m2 = cv2.threshold(u2_alpha, 30, 255, cv2.THRESH_BINARY)
    combined = cv2.bitwise_or(m1, m2)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    return clean_mask_largest(combined)


def strategy_u2net_only(img_pil, u2net_session):
    """Round 2: u2net only (tighter mask, less table)."""
    rgba = remove(img_pil, session=u2net_session)
    alpha = np.array(rgba.split()[3])
    return clean_mask_largest(alpha, threshold=50)


def strategy_inspyrenet_only(img_pil, inspyrenet_remover):
    """Round 3: InSPyReNet only."""
    result = inspyrenet_remover.process(img_pil, type='map')
    mask = np.array(result)
    return clean_mask_largest(mask)


def strategy_birefnet(img_pil, birefnet_session):
    """Round 4: birefnet-general."""
    rgba = remove(img_pil, session=birefnet_session)
    alpha = np.array(rgba.split()[3])
    return clean_mask_largest(alpha, threshold=30)


# ========== ORIENTATION + COMPOSITING ==========

def detect_rump_direction(mask):
    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return 'bottom'
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    H = y_max - y_min + 1
    W = x_max - x_min + 1
    cropped = mask[y_min:y_max + 1, x_min:x_max + 1]
    pct = 0.20

    slice_h = max(1, int(H * pct))
    top_spans = []
    for r in range(slice_h):
        px = np.where(cropped[r, :] > 0)[0]
        if len(px) > 0:
            top_spans.append(px.max() - px.min() + 1)
    max_top = max(top_spans) if top_spans else 0

    bottom_spans = []
    for r in range(H - slice_h, H):
        px = np.where(cropped[r, :] > 0)[0]
        if len(px) > 0:
            bottom_spans.append(px.max() - px.min() + 1)
    max_bottom = max(bottom_spans) if bottom_spans else 0

    slice_w = max(1, int(W * pct))
    left_spans = []
    for c in range(slice_w):
        px = np.where(cropped[:, c] > 0)[0]
        if len(px) > 0:
            left_spans.append(px.max() - px.min() + 1)
    max_left = max(left_spans) if left_spans else 0

    right_spans = []
    for c in range(W - slice_w, W):
        px = np.where(cropped[:, c] > 0)[0]
        if len(px) > 0:
            right_spans.append(px.max() - px.min() + 1)
    max_right = max(right_spans) if right_spans else 0

    if H > W:
        return 'top' if max_top > max_bottom else 'bottom'
    else:
        return 'left' if max_left > max_right else 'right'


def composite_with_shadow(cropped_cowhide, target_size, padding_pct=0.08):
    S = target_size
    max_fit = int(S * (1 - 2 * padding_pct))
    w, h = cropped_cowhide.size
    scale = min(max_fit / w, max_fit / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cropped_cowhide.resize((nw, nh), Image.Resampling.LANCZOS)

    sf = S / 1500.0
    dx, dy = int(-12 * sf), int(12 * sf)
    blur_r = max(3, int(6 * sf))

    alpha = resized.split()[3]
    shadow_mask = Image.eval(alpha, lambda a: int(a * 0.18))
    canvas = Image.new('RGBA', (S, S), (255, 255, 255, 255))
    x_pos, y_pos = (S - nw) // 2, (S - nh) // 2

    shadow_canvas = Image.new('L', (S, S), 0)
    shadow_canvas.paste(shadow_mask, (x_pos + dx, y_pos + dy), mask=alpha)
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(blur_r))

    shadow_rgba = Image.new('RGBA', (S, S), (0, 0, 0, 255))
    canvas.paste(shadow_rgba, (0, 0), mask=shadow_canvas)
    canvas.paste(resized, (x_pos, y_pos), mask=resized)
    return canvas.convert('RGB')


def process_image(img_path, mask_func):
    """Process a single image: segment, orient, sharpen, composite."""
    img = Image.open(img_path)
    img = ImageOps.exif_transpose(img)
    orig_w, orig_h = img.size

    # Segment
    mask = mask_func(img)

    # Orient
    img_rgba = Image.merge("RGBA", (*img.split()[:3], Image.fromarray(mask)))
    rump_dir = detect_rump_direction(mask)
    rot_map = {'bottom': 0, 'top': 180, 'left': 270, 'right': 90}
    rot = rot_map.get(rump_dir, 0)
    if rot != 0:
        img_rgba = img_rgba.rotate(-rot, expand=True)

    # Crop
    bbox = img_rgba.getbbox()
    if not bbox:
        bbox = (0, 0, img_rgba.width, img_rgba.height)
    cropped = img_rgba.crop(bbox)

    # Sharpen
    sharpened = cropped.filter(ImageFilter.UnsharpMask(radius=2.0, percent=180, threshold=1))

    # Composite
    comp_1500 = composite_with_shadow(sharpened, 1500)
    max_dim = max(orig_w, orig_h)
    comp_orig = composite_with_shadow(sharpened, max_dim)

    return comp_orig, comp_1500, max_dim, rump_dir


def main():
    print("=" * 60)
    print("ITERATIVE PIPELINE WITH GEMINI QC")
    print("=" * 60)

    images = sorted([f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
    print(f"Found {len(images)} images.\n")

    # Load models
    print("Loading models...")
    inspyrenet_remover = Remover()
    u2net_session = new_session('u2net')
    birefnet_session = None  # Lazy load
    print("Models ready!\n")

    # Define rounds
    rounds = [
        ("Round 1: Hybrid (InSPyReNet + u2net)", 
         lambda img: strategy_hybrid(img, inspyrenet_remover, u2net_session)),
        ("Round 2: u2net only (tight mask)",
         lambda img: strategy_u2net_only(img, u2net_session)),
        ("Round 3: InSPyReNet only",
         lambda img: strategy_inspyrenet_only(img, inspyrenet_remover)),
    ]

    pending = list(images)  # Files still to process
    approved_count = 0
    all_results = {}  # filename -> {round, issues, etc}

    for round_idx, (round_name, mask_func) in enumerate(rounds):
        if not pending:
            break

        print(f"\n{'=' * 60}")
        print(f"{round_name} - {len(pending)} images to process")
        print(f"{'=' * 60}")

        still_pending = []

        for idx, fname in enumerate(pending):
            base = os.path.splitext(fname)[0]
            out_name = f"{base}{NAME_SUFFIX}.jpg"
            out_1500 = os.path.join(APPROVED_1500_DIR, out_name)
            out_orig = os.path.join(APPROVED_ORIG_DIR, out_name)

            print(f"\n  [{idx+1}/{len(pending)}] {fname}")
            src_path = os.path.join(SRC_DIR, fname)

            try:
                # Process
                comp_orig, comp_1500, max_dim, rump_dir = process_image(src_path, mask_func)

                # Save temp for verification
                temp_path = os.path.join(APPROVED_1500_DIR, f"_temp_{fname}")
                comp_1500.save(temp_path, "JPEG", quality=90)

                # Gemini verification
                print(f"    Orientation: rump={rump_dir}")
                print(f"    Verifying with Gemini...", end=" ")
                result = verify_with_gemini(temp_path)

                if result.get("approved", False):
                    print(f"APPROVED (confidence: {result.get('confidence', '?')})")
                    # Save final
                    comp_1500.save(out_1500, "JPEG", quality=90)
                    comp_orig.save(out_orig, "JPEG", quality=90)
                    approved_count += 1
                    all_results[fname] = {"round": round_idx + 1, "status": "approved"}
                else:
                    issues = result.get("issues", ["unknown"])
                    print(f"REJECTED: {'; '.join(issues)}")
                    still_pending.append(fname)
                    all_results[fname] = {"round": round_idx + 1, "status": "rejected", "issues": issues}

                # Clean temp
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            except Exception as e:
                print(f"    ERROR: {e}")
                still_pending.append(fname)
                all_results[fname] = {"round": round_idx + 1, "status": "error", "issues": [str(e)]}

            # Rate limit for Gemini API
            time.sleep(0.5)

        pending = still_pending
        print(f"\n  {round_name} complete: {len(pending)} still pending")

    # Try birefnet for any remaining
    if pending:
        print(f"\n{'=' * 60}")
        print(f"Round 4: birefnet-general - {len(pending)} images")
        print(f"{'=' * 60}")

        print("Loading birefnet model...")
        birefnet_session = new_session('birefnet-general')

        for idx, fname in enumerate(pending):
            base = os.path.splitext(fname)[0]
            out_name = f"{base}{NAME_SUFFIX}.jpg"
            out_1500 = os.path.join(APPROVED_1500_DIR, out_name)
            out_orig = os.path.join(APPROVED_ORIG_DIR, out_name)

            print(f"\n  [{idx+1}/{len(pending)}] {fname}")
            src_path = os.path.join(SRC_DIR, fname)

            try:
                mask_func = lambda img: strategy_birefnet(img, birefnet_session)
                comp_orig, comp_1500, max_dim, rump_dir = process_image(src_path, mask_func)

                # Save regardless (last round)
                comp_1500.save(out_1500, "JPEG", quality=90)
                comp_orig.save(out_orig, "JPEG", quality=90)

                # Verify
                result = verify_with_gemini(out_1500)
                status = "approved" if result.get("approved") else "best_effort"
                issues = result.get("issues", [])
                print(f"    Status: {status} - {'; '.join(issues) if issues else 'OK'}")
                all_results[fname] = {"round": 4, "status": status, "issues": issues}

            except Exception as e:
                print(f"    ERROR: {e}")
                # Fall back to round 1 result
                all_results[fname] = {"round": 4, "status": "error", "issues": [str(e)]}

            time.sleep(0.5)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"FINAL SUMMARY")
    print(f"{'=' * 60}")

    by_round = {}
    for fname, info in all_results.items():
        r = info["round"]
        s = info["status"]
        by_round.setdefault(r, {"approved": 0, "rejected": 0, "best_effort": 0, "error": 0})
        by_round[r][s] = by_round[r].get(s, 0) + 1

    for r in sorted(by_round.keys()):
        stats = by_round[r]
        print(f"  Round {r}: approved={stats.get('approved',0)}, rejected={stats.get('rejected',0)}, best_effort={stats.get('best_effort',0)}, errors={stats.get('error',0)}")

    total_approved = sum(1 for v in all_results.values() if v["status"] in ("approved", "best_effort"))
    print(f"\n  Total: {total_approved}/{len(images)} saved to approved folders")
    print(f"  Output: {APPROVED_1500_DIR}")

    # Save report
    report_path = os.path.join(PARENT_DIR, "batch2_qc_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"  Report: {report_path}")


if __name__ == "__main__":
    main()
