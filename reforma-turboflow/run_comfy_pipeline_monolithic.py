import os
import sys
import re
import json
import base64
import requests
import numpy as np
import torch
import shutil
from io import BytesIO
from PIL import Image
from pathlib import Path

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Try importing SAM3 predictor as fallback
try:
    from ultralytics.models.sam import SAM3SemanticPredictor
    SAM3_AVAILABLE = True
    print("SAM3SemanticPredictor imported successfully.")
except Exception as e:
    print("Warning: Could not import SAM3SemanticPredictor. SAM3 fallback will be unavailable:", e)
    SAM3_AVAILABLE = False

from comfy_client import ComfyClient

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full")
BRAND_DICT_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\brand_sku_dict.json"
GEMINI_ENV_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

# Fallback for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

def load_gemini_key():
    if os.path.exists(GEMINI_ENV_PATH):
        with open(GEMINI_ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

def normalize_name(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def clean_offwhite_background(img, bg_color):
    img_arr = np.array(img.convert('RGB')).astype(np.float32)
    bg_color = np.array(bg_color).astype(np.float32)
    
    # Calculate pixel distance from bg_color
    diff = np.sum(np.abs(img_arr - bg_color), axis=-1)
    
    # Soft mask: 0.0 at bg_color, 1.0 far away
    # Using a threshold of 15.0 and transition width of 80.0
    color_mask = np.clip((diff - 15.0) / 80.0, 0.0, 1.0)
    color_mask = np.expand_dims(color_mask, axis=-1)
    
    # Normalize/brighten to map bg_color to 255
    scale = 255.0 / np.clip(bg_color - 2.0, 1.0, 255.0)
    normalized = np.clip(img_arr * scale, 0, 255)
    
    # Desaturate
    gray = 0.299 * normalized[:,:,0] + 0.587 * normalized[:,:,1] + 0.114 * normalized[:,:,2]
    gray_img = np.stack([gray, gray, gray], axis=-1)
    
    # Blend: desaturated normalized for bg/shadow, normalized color for product
    final_arr = normalized * color_mask + gray_img * (1.0 - color_mask)
    return Image.fromarray(np.round(final_arr).astype(np.uint8))

def load_and_ensure_size(img):
    w, h = img.size
    max_dim = max(w, h)
    if max_dim < 2000:
        scale = 2000.0 / max_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), RESAMPLING_METHOD)
    return img

def classify_and_size_product(folder_name):
    folder_lower = folder_name.lower()
    # SOFA
    is_sofa = False
    if "soffa" in folder_lower or "sofa" in folder_lower or "baddsoffa" in folder_lower or "bäddsoffa" in folder_lower or "schaslong" in folder_lower:
        is_sofa = True
    if is_sofa:
        is_2_seat = any(x in folder_lower for x in ["2-sits", "2-seater", "2sits", "2seater", "loveseat", "love-seat", "baddfatolj", "bäddfåtölj"])
        if is_2_seat:
            return "sofa_2_seat", 0.92, 0.42, 0.10, False
        else:
            return "sofa_3_seat", 0.94, 0.42, 0.10, False

    # CHAIRS, ARMCHAIRS, BARSTOOLS, STOOLS
    is_chair = any(x in folder_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"])
    if is_chair:
        if any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol"]):
            return "armchair", 0.92, 0.82, 0.10, False
        elif "barstol" in folder_lower:
            return "barstool", 0.75, 0.86, 0.10, False
        elif any(x in folder_lower for x in ["pall", "puff", "sittpuff"]):
            return "stool", 0.48, 0.52, 0.10, False
        else:
            return "chair_dining", 0.90, 0.82, 0.10, False

    # TABLES
    is_table = any(x in folder_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord"])
    if is_table:
        is_dining = any(x in folder_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"])
        if is_dining:
            return "table_large", 0.92, 0.52, 0.10, False
        else:
            return "table_small", 0.83, 0.45, 0.10, False

    # CABINETS
    is_cabinet = any(x in folder_lower for x in ["skap", "skåp", "byra", "byrå", "sideboard", "skank", "skänk", "garderob", "tv-bank", "tv-bänk", "vinhylla"])
    if is_cabinet:
        is_large = any(x in folder_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ"]) or ("skap" in folder_lower or "skåp" in folder_lower) and not any(x in folder_lower for x in ["sido", "litet", "byra", "byrå"])
        if is_large:
            return "cabinet_large", 0.83, 0.92, 0.10, False
        else:
            return "cabinet_small", 0.92, 0.63, 0.10, False

    # SHELVES
    is_shelf = any(x in folder_lower for x in ["hylla", "hyllor", "vagghylla", "vägghylla", "vagghyllor", "vägghyllor"])
    if is_shelf:
        is_wall = any(x in folder_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"])
        if is_wall:
            return "shelf_hanging", 0.81, 0.40, 0.50, True
        else:
            return "shelf_floor", 0.86, 0.86, 0.10, False

    # LIGHTING
    is_lamp = any(x in folder_lower for x in ["lamp", "lampa", "belysning", "ljus", "stjarna", "stjärna", "advent"])
    if is_lamp:
        if "golv" in folder_lower:
            return "lamp_floor", 0.63, 0.90, 0.10, False
        elif "bord" in folder_lower:
            return "lamp_table", 0.38, 0.44, 0.50, True
        elif any(x in folder_lower for x in ["taklampa", "pendel", "krona", "plafond", "adventstjarna", "adventstjärna", "stjarna", "stjärna", "oslo", "sally", "lotus"]):
            return "lamp_pendant", 0.70, 0.58, 0.50, True
        elif "vagg" in folder_lower or "vägg" in folder_lower:
            return "lamp_wall", 0.58, 0.46, 0.50, True
        else:
            return "lamp_pendant", 0.70, 0.58, 0.50, True

    # DEFAULT
    return "default", 0.86, 0.90, 0.50, True

def adjust_size_by_name(category, name, target_w, target_h):
    name_lower = name.lower()
    name_clean = re.sub(r'(202[0-9]|26u)', '', name_lower)
    numbers = re.findall(r'\d+', name_clean)
    m_cross = re.search(r'(\d+)\s*x\s*(\d+)', name_clean)
    
    if category == "table_large":
        length = 180
        if m_cross:
            length = int(m_cross.group(1))
        else:
            for num in map(int, numbers):
                if 100 <= num <= 260:
                    length = num
                    break
        scale = length / 180.0
        target_w = target_w * scale
        target_w = max(0.70, min(0.94, target_w))
    elif category == "shelf_hanging":
        width = 75
        for num in map(int, numbers):
            if 15 <= num <= 150:
                width = num
                break
        scale = width / 75.0
        target_w = target_w * scale
        target_w = max(0.65, min(0.94, target_w))
    elif category == "cabinet_large":
        height = 180
        if m_cross:
            height = int(m_cross.group(2))
        else:
            for num in map(int, numbers):
                if 100 <= num <= 240:
                    height = num
                    break
        scale = height / 180.0
        target_h = target_h * scale
        target_h = max(0.70, min(0.94, target_h))
    return target_w, target_h

def query_gemini_for_classification(img_path, key):
    try:
        with Image.open(img_path) as img:
            img_resized = img.resize((500, 500))
            buffered = BytesIO()
            img_resized.convert('RGB').save(buffered, format="JPEG", quality=80)
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        prompt = (
            "Is this image a STUDIO product shot (the furniture item is isolated on a plain white, light gray, or seamless studio backdrop) "
            "or a LIFESTYLE shot (the furniture item is shown inside a furnished or decorated room/interior with floors, walls, windows, plants, or other decor)? "
            "Reply strictly in JSON format:\n"
            "{\n"
            "  \"type\": \"studio\" | \"lifestyle\"\n"
            "}"
        )
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }
        res = requests.post(url, headers=headers, json=data, timeout=20)
        if res.status_code == 200:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            classification = json.loads(text_resp)
            return classification.get("type", "studio")
    except Exception as e:
        print(f"  [Classifier Warning] Gemini classification failed: {e}")
    return "studio"

def query_gemini_for_zoom_status(img_path, key):
    try:
        with Image.open(img_path) as img:
            img_resized = img.resize((500, 500))
            buffered = BytesIO()
            img_resized.convert('RGB').save(buffered, format="JPEG", quality=80)
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        prompt = (
            "Analyze this furniture product image. Is it a full view of the product "
            "(showing the entire piece of furniture standing in the frame, such as a front, back, side, or three-quarter view) "
            "or is it a close-up/detail/technical view (such as a close-up of the fabric texture, a leg, a drawer handle, wood grain, "
            "or a sketch/dimension blueprint drawing)?\n\n"
            "Reply strictly in JSON format:\n"
            "{\n"
            "  \"is_zoom_or_detail\": true | false\n"
            "}"
        )
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }
        res = requests.post(url, headers=headers, json=data, timeout=20)
        if res.status_code == 200:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            classification = json.loads(text_resp)
            return classification.get("is_zoom_or_detail", False)
    except Exception as e:
        print(f"  [Classifier Warning] Gemini zoom classification failed: {e}")
    return False

def classify_image_type_robust(img_path, gemini_key=None):
    try:
        img = Image.open(img_path).convert('RGB')
        img_small = img.resize((300, 300))
        arr = np.array(img_small)
        border_width = 15
        top = arr[:border_width, :, :]
        bottom = arr[-border_width:, :, :]
        left = arr[border_width:-border_width, :border_width, :]
        right = arr[border_width:-border_width, -border_width:, :]
        
        border_pixels = np.concatenate([
            top.reshape(-1, 3),
            bottom.reshape(-1, 3),
            left.reshape(-1, 3),
            right.reshape(-1, 3)
        ], axis=0)
        
        luma = 0.299 * border_pixels[:, 0] + 0.587 * border_pixels[:, 1] + 0.114 * border_pixels[:, 2]
        mean_luma = np.mean(luma) / 255.0
        std_luma = np.std(luma) / 128.0
        
        rgb_max = np.max(border_pixels, axis=1)
        rgb_min = np.min(border_pixels, axis=1)
        sat = (rgb_max - rgb_min) / 255.0
        mean_sat = np.mean(sat)
        
        white_pixel_ratio = np.mean(luma > 240.0)
        print(f"  [Classifier] Metrics: luma={mean_luma:.3f}, std_luma={std_luma:.3f}, sat={mean_sat:.3f}, white_ratio={white_pixel_ratio:.3f}")
        
        if white_pixel_ratio > 0.30 and mean_sat < 0.08:
            if std_luma > 0.15:
                if gemini_key:
                    print("  [Classifier] Border contact detected on white backdrop. Falling back to Gemini...")
                    return query_gemini_for_classification(img_path, gemini_key)
                else:
                    return "studio"
            return "studio"
            
        if mean_luma > 0.94 and std_luma < 0.10 and mean_sat < 0.06:
            return "studio"
        if mean_luma < 0.80 or mean_sat > 0.15 or std_luma > 0.25:
            return "lifestyle"
            
        if gemini_key:
            print("  [Classifier] Ambiguous metrics. Falling back to Gemini classification...")
            return query_gemini_for_classification(img_path, gemini_key)
            
        return "studio" if mean_luma > 0.88 else "lifestyle"
    except Exception as e:
        print(f"  [Classifier Error] Heuristic classification failed: {e}")
        return "studio"

def make_qa_comparison_image(orig_pil, cutout_pil):
    orig_res = orig_pil.resize((1000, 1000), RESAMPLING_METHOD)
    cutout_res = cutout_pil.resize((1000, 1000), RESAMPLING_METHOD)
    magenta_bg = Image.new("RGB", (1000, 1000), (255, 0, 255))
    if cutout_res.mode == "RGBA":
        magenta_bg.paste(cutout_res, mask=cutout_res.split()[3])
    else:
        magenta_bg.paste(cutout_res)
    combined = Image.new("RGB", (2000, 1000))
    combined.paste(orig_res, (0, 0))
    combined.paste(magenta_bg, (1000, 0))
    return combined

def run_gemini_self_review(orig_path, cutout_pil, key):
    try:
        orig_pil = Image.open(orig_path)
        comparison_img = make_qa_comparison_image(orig_pil, cutout_pil)
        
        # Save to disk for debugging
        try:
            os.makedirs("scratch", exist_ok=True)
            comparison_img.save("scratch/qa_last_comparison.jpg", format="JPEG", quality=85)
        except Exception as e:
            print(f"  [QA Debug Warning] Could not save last QA comparison: {e}")
            
        buffered = BytesIO()
        comparison_img.save(buffered, format="JPEG", quality=80)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        prompt = (
            "You are a quality control AI for an e-commerce catalog. Look at this side-by-side comparison:\n"
            "- Left: The original product image.\n"
            "- Right: The cutout product image placed on a bright magenta (#FF00FF) background.\n"
            "Analyze if the cutout was successful or has defects.\n"
            "Defect types:\n"
            "1. 'amputation': Essential parts of the product are cut off or missing in the cutout (e.g. thin legs of a chair are gone, table top is sliced, etc.).\n"
            "2. 'background_residue': Pieces of the original background, wall, or floor are still visible on the magenta background around the product.\n"
            "3. 'halo_fringe': The edges of the product itself are highly jagged, pixelated, or show a color halo from the original background. NOTE: The cutout contains an intentional soft black drop shadow which blends around the product's silhouette (especially at the bottom, but it may also bleed slightly to the sides and top as a soft, blurry black/grey shadow). This soft black shadow is INTENTIONAL and must NOT be flagged as a halo/fringe defect. Only flag jagged, pixelated, or 'dirty' edges, or parts of the original white/grey background. If the edges show a smooth, soft, blurry black/grey shadow, it is a PASS.\n"
            "\n"
            "Reply strictly in JSON format:\n"
            "{\n"
            "  \"status\": \"pass\" | \"fail\",\n"
            "  \"defect_type\": \"none\" | \"amputation\" | \"background_residue\" | \"halo_fringe\",\n"
            "  \"reason\": \"A brief description of why it failed or passed\"\n"
            "}"
        )
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            return json.loads(text_resp)
    except Exception as e:
        print(f"  [QA Loop Warning] Gemini self-review failed: {e}")
    return {"status": "pass", "defect_type": "none", "reason": "Self-review failed to run, assuming pass"}

def get_adjusted_parameters(defect_type, attempt):
    params = {}
    if defect_type == "amputation":
        params = {
            "MASK_REFINER": {
                "mask_edge_erode": max(1, 6 - 2 * attempt),
                "mask_edge_dilate": min(12, 4 + 2 * attempt),
                "transparent_trimap_erode": 48,
                "transparent_trimap_dilate": 96
            },
            "BIREFNET": {
                "alpha_matting_foreground_threshold": 245
            }
        }
    elif defect_type == "background_residue":
        params = {
            "MASK_REFINER": {
                "mask_edge_erode": min(20, 6 + 3 * attempt),
                "mask_edge_dilate": max(0, 4 - 2 * attempt)
            },
            "BIREFNET": {
                "alpha_matting_background_threshold": 5
            }
        }
    elif defect_type == "halo_fringe":
        params = {
            "MASK_REFINER": {
                "trimap_blur": min(12, 4 + 2 * attempt),
                "white_point": 0.95,
                "black_point": 0.05
            }
        }
    return params

def save_as_jpg(pil_img, dest_path, target_size, quality=90):
    img_copy = pil_img.copy()
    if img_copy.mode in ('RGBA', 'LA') or (img_copy.mode == 'P' and 'transparency' in img_copy.info):
        background = Image.new("RGB", img_copy.size, (255, 255, 255))
        background.paste(img_copy, mask=img_copy.split()[3] if img_copy.mode == 'RGBA' else None)
        img_copy = background
    else:
        img_copy = img_copy.convert("RGB")
    
    # Resize keeping aspect ratio
    w, h = img_copy.size
    longest = max(w, h)
    if longest > target_size:
        scale = float(target_size) / longest
        img_copy = img_copy.resize((int(w * scale), int(h * scale)), RESAMPLING_METHOD)
    img_copy.save(dest_path, "JPEG", quality=quality)

def extract_slot_from_filename(filename):
    fn_lower = filename.lower()
    m_double_wonder = re.search(r'-(\d+)-(\d+)-wonder', fn_lower)
    if m_double_wonder:
        return int(m_double_wonder.group(2))
    m_double_w_wonder = re.search(r'-(\d+)-(\d+)-w-wonder', fn_lower)
    if m_double_w_wonder:
        return int(m_double_w_wonder.group(2))
    m_w_wonder = re.search(r'-(\d+)-w-wonder', fn_lower)
    if m_w_wonder:
        return int(m_w_wonder.group(1))
    m_wonder_w = re.search(r'-(\d+)-wonder-w', fn_lower)
    if m_wonder_w:
        return int(m_wonder_w.group(1))
    m_w = re.search(r'-(\d+)-w', fn_lower)
    if m_w:
        return int(m_w.group(1))
    m_digit = re.search(r'[-_](\d+)\.[a-z]+$', fn_lower)
    if m_digit:
        return int(m_digit.group(1))
    return None

def is_processed_render(filename):
    fn_lower = filename.lower()
    has_double_index = re.search(r'-(\d+)-(\d+)-?w?', fn_lower) is not None
    has_wonder = 'wonder' in fn_lower
    if fn_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
        if has_wonder:
            return True
        if not has_double_index:
            if '-w-' in fn_lower or '-w.' in fn_lower or fn_lower.endswith(('-w.jpg', '-w.jpeg')):
                return True
    return False

# Local SAM3 crop fallback (for robust resilience)
def process_image_sam3_fallback(predictor, img_resized, category, target_w_fill, target_h_fill, floor_pct, is_centered, text_prompts):
    w, h = img_resized.size
    is_wb, bg_color = False, None
    try:
        # Check white background
        img_rgb = img_resized.convert('RGB')
        arr = np.array(img_rgb)
        patches = [arr[10:25, 10:25], arr[10:25, -25:-10], arr[-25:-10, 10:25], arr[-25:-10, -25:-10]]
        means = [np.mean(pat, axis=(0,1)) for pat in patches]
        means.sort(key=lambda c: np.sum(c))
        bg_color = np.mean(means[1:], axis=0)
        bg_mean = np.mean(bg_color)
        grays = [0.299*m[0] + 0.587*m[1] + 0.114*m[2] for m in means[1:]]
        std_dev = np.std(grays)
        is_wb = (bg_mean > 210) and (std_dev < 15.0)
    except Exception:
        pass

    cleaned_shadow = img_resized
    if is_wb and bg_color is not None:
        cleaned_shadow = clean_offwhite_background(img_resized, bg_color)
        
    bbox_clean = None
    try:
        with torch.no_grad():
            results = predictor(img_resized, text=text_prompts)
        if len(results) > 0 and results[0].masks is not None:
            masks_tensor = results[0].masks.data
            combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy()
            combined_mask[:15, :] = False
            combined_mask[-15:, :] = False
            combined_mask[:, :15] = False
            combined_mask[:, -15:] = False
            coords_body = np.argwhere(combined_mask > 0)
            if coords_body.size > 0:
                y_min_clean = coords_body[:, 0].min()
                y_max_clean = coords_body[:, 0].max()
                x_min_clean = coords_body[:, 1].min()
                x_max_clean = coords_body[:, 1].max()
                bbox_clean = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
                
                # Restore original product pixels inside the body mask!
                mask_pil = Image.fromarray((combined_mask * 255).astype(np.uint8), mode='L')
                cleaned_shadow = Image.composite(img_resized, cleaned_shadow, mask_pil)
    except Exception:
        pass

    if bbox_clean is not None:
        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
        arr = np.array(cleaned_shadow.convert('RGB'))
        non_white = np.any(arr < 254, axis=-1)
        non_white[:5, :] = False
        non_white[-5:, :] = False
        non_white[:, :5] = False
        non_white[:, -5:] = False
        
        coords_shadow = np.argwhere(non_white)
        if coords_shadow.size > 0:
            y_min_raw = coords_shadow[:, 0].min()
            y_max_raw = coords_shadow[:, 0].max()
            x_min_raw = coords_shadow[:, 1].min()
            x_max_raw = coords_shadow[:, 1].max()
        else:
            y_min_raw, y_max_raw, x_min_raw, x_max_raw = y_min_clean, y_max_clean, x_min_clean, x_max_clean
            
        crop_x_min = max(0, x_min_raw - 40)
        crop_y_min = max(0, y_min_raw - 20)
        crop_x_max = min(w, x_max_raw + 40)
        crop_y_max = min(h, y_max_raw + 20)
        
        cropped = cleaned_shadow.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
        W_p = x_max_clean - x_min_clean
        H_p = y_max_clean - y_min_clean
        
        # Category-dependent scaling
        scale_w = (target_w_fill * 2000.0) / W_p
        scale_h = (target_h_fill * 2000.0) / H_p
        scale = min(scale_w, scale_h)
            
        # Apply safety limits
        if W_p * scale > 1900.0:
            scale = 1900.0 / W_p
            
        if is_centered:
            if H_p * scale > 1900.0:
                scale = 1900.0 / H_p
        else:
            max_h_allowed = int(2000 - (floor_pct * 2000) - 50)
            if H_p * scale > max_h_allowed:
                scale = max_h_allowed / H_p
                
        new_w_body = int(W_p * scale)
        new_h_body = int(H_p * scale)
                
        new_w_crop = int((crop_x_max - crop_x_min) * scale)
        new_h_crop = int((crop_y_max - crop_y_min) * scale)
        cropped_resized = cropped.resize((new_w_crop, new_h_crop), RESAMPLING_METHOD)
        
        canvas = Image.new("RGB", (2000, 2000), (255, 255, 255))
        paste_x_body = (2000 - new_w_body) // 2
        
        if not is_centered:
            paste_y_body = int(2000 - (floor_pct * 2000) - new_h_body)
        else:
            paste_y_body = (2000 - new_h_body) // 2
            
        offset_x = x_min_clean - crop_x_min
        offset_y = y_min_clean - crop_y_min
        
        paste_x = paste_x_body - int(offset_x * scale)
        paste_y = paste_y_body - int(offset_y * scale)
        canvas.paste(cropped_resized, (paste_x, paste_y))
        return canvas
        
    return img_resized.resize((2000, 2000), RESAMPLING_METHOD)

def get_sam3_text_prompt(category, prod_name):
    prompts = ["furniture"]
    prod_name_lower = prod_name.lower()
    if "soffa" in prod_name_lower or "sofa" in prod_name_lower or "schaslong" in prod_name_lower:
        prompts = ["sofa", "couch", "furniture"]
    elif "stol" in prod_name_lower or "chair" in prod_name_lower or "armchair" in prod_name_lower:
        prompts = ["chair", "armchair", "furniture"]
    elif "pall" in prod_name_lower or "puff" in prod_name_lower or "stool" in prod_name_lower:
        prompts = ["stool", "pouffe", "furniture"]
    elif "bord" in prod_name_lower or "table" in prod_name_lower or "desk" in prod_name_lower:
        prompts = ["table", "desk", "furniture"]
    elif "skåp" in prod_name_lower or "skap" in prod_name_lower or "byrå" in prod_name_lower or "byra" in prod_name_lower or "sideboard" in prod_name_lower or "skänk" in prod_name_lower or "tv-bänk" in prod_name_lower or "tv-bank" in prod_name_lower or "cabinet" in prod_name_lower:
        prompts = ["cabinet", "sideboard", "cupboard", "furniture"]
    elif "vinhylla" in prod_name_lower or "wine" in prod_name_lower:
        prompts = ["wine rack", "cabinet", "furniture"]
    elif "hylla" in prod_name_lower or "shelf" in prod_name_lower or "shelves" in prod_name_lower or "bookcase" in prod_name_lower:
        prompts = ["shelf", "bookcase", "shelves", "furniture"]
    elif "lampa" in prod_name_lower or "lamp" in prod_name_lower or "belysning" in prod_name_lower:
        prompts = ["lamp", "light fixture", "furniture"]
    return prompts

def main():
    print("==================================================")
    print("     COMFYUI COGNITIVE CUTOUT & TUNING PIPELINE   ")
    print("==================================================")
    
    is_dry_run = "--dry-run" in sys.argv
    gemini_key = load_gemini_key()
    if not gemini_key:
        print("[WARNING] GEMINI_API_KEY.env not found or invalid. Gemini QA & fallback classifier will be disabled.")
    else:
        print("Gemini API Key loaded successfully.")
        
    comfy_client = ComfyClient()
    comfy_online = comfy_client.check_server_status()
    if not comfy_online:
        print("[WARNING] ComfyUI local server is down. Running entirely in SAM3 fallback mode.")
    else:
        print("ComfyUI server is online and connected.")

    if not os.path.exists(BRAND_DICT_PATH):
        print(f"[ERROR] Brand dictionary not found: {BRAND_DICT_PATH}")
        return
        
    # Filter arguments early
    limit_sku = None
    limit_val = None
    for arg in sys.argv:
        if arg.startswith("--sku="):
            limit_sku = arg.split("=")[1].strip()
        elif arg.startswith("--limit="):
            try:
                limit_val = int(arg.split("=")[1].strip())
            except ValueError:
                pass

    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
        
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    if not is_dry_run:
        print(f"Ensuring staging directories exist: {FTP_UPLOAD_DIR}")
        for d in (artiklar_dir, liten_dir, zoom_dir):
            os.makedirs(d, exist_ok=True)
            for f in os.listdir(d):
                p_file = os.path.join(d, f)
                if os.path.isfile(p_file):
                    # Only remove if no SKU limit is set, or if the file belongs to this SKU
                    if limit_sku is None or f.startswith(limit_sku):
                        try:
                            os.remove(p_file)
                        except Exception:
                            pass
    else:
        print("\n*** RUNNING IN DRY-RUN MODE (first 10 items processed, no output files written) ***")
        
    # Initialize SAM3 Predictor if available
    predictor = None
    if SAM3_AVAILABLE:
        print("Initializing SAM 3 semantic predictor on CUDA (Fallback node)...")
        try:
            overrides = dict(model="sam3.pt", conf=0.10, device="cuda")
            predictor = SAM3SemanticPredictor(overrides=overrides)
            print("SAM 3 Predictor successfully loaded on GPU.")
        except Exception as e:
            print(f"Error loading SAM 3 predictor fallback: {e}")

    # Scan directories exactly as before
    wb_fix_folders = {}
    if os.path.exists(NEW_WHITE_BG_DIR):
        for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
            for d in dirs:
                dir_path = os.path.join(root, d)
                has_img = any(f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)))
                if has_img:
                    norm = normalize_name(d)
                    wb_fix_folders[norm] = dir_path
                    
    topaz_files = {}
    if os.path.exists(TOPAZ_DIR):
        for f in os.listdir(TOPAZ_DIR):
            if f.lower().endswith('.webp'):
                m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
                if m:
                    prod_name = m.group(1)
                    slot = int(m.group(2))
                    norm = normalize_name(prod_name)
                    if norm not in topaz_files:
                        topaz_files[norm] = []
                    topaz_files[norm].append((slot, os.path.join(TOPAZ_DIR, f)))
                    
    orig_folders = {}
    orig_sku_folders = {}
    if os.path.exists(ORIG_DIR):
        for folder in os.listdir(ORIG_DIR):
            p = os.path.join(ORIG_DIR, folder, "artiklar")
            if os.path.isdir(p):
                norm = normalize_name(folder)
                orig_folders[norm] = p
                sku_match = re.search(r'\(([^)]+)\)', folder)
                if sku_match:
                    sku = sku_match.group(1).strip().lower()
                    orig_sku_folders[sku] = p

    processed_count = 0
    skipped_count = 0
    products_to_process = list(brand_sku_dict.items())
    
    # Filter arguments (already parsed early)
            
    if limit_sku:
        products_to_process = [(name, info) for name, info in products_to_process if info['sku'].strip().lower() == limit_sku.lower()]
        print(f"Limiting processing to SKU: {limit_sku}. Found matches: {len(products_to_process)}")
    elif limit_val is not None:
        products_to_process = products_to_process[:limit_val]
        print(f"Limiting processing to first {limit_val} items.")
    elif is_dry_run:
        products_to_process = products_to_process[:10]
        
    print(f"\nProcessing {len(products_to_process)} total catalog products...")
    workflow_path = Path("comfy_workflows/furniture_refiner.api.json")
    temp_output_path = Path("scratch/comfy_cutout_temp.png")

    for idx, (prod_name, info) in enumerate(products_to_process):
        sku = info['sku']
        sku_clean = sku.strip()
        
        if sku_clean == "1100476" or "lionel" in prod_name.lower():
            print(f"[{idx+1}/{len(products_to_process)}] Skipping Lionel Chair (SKU: {sku_clean}) - Discontinued.")
            continue
        if any(x in prod_name.lower() for x in ["matta", "mattor", "rug", "carpet"]):
            print(f"[{idx+1}/{len(products_to_process)}] Skipping Rug (SKU: {sku_clean}) - '{prod_name}'.")
            continue
            
        print(f"\n[{idx+1}/{len(products_to_process)}] Mapping product: '{prod_name}' -> SKU: {sku_clean}")
        prod_norm = normalize_name(prod_name)
        processed_slots = {}
        
        # 1. Load Baseline Fallback (3rd priority)
        dir_path = None
        if prod_norm in orig_folders:
            dir_path = orig_folders[prod_norm]
        elif sku_clean.lower() in orig_sku_folders:
            dir_path = orig_sku_folders[sku_clean.lower()]
        if dir_path:
            for f in os.listdir(dir_path):
                p = os.path.join(dir_path, f)
                if os.path.isfile(p) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    processed_slots[1] = p
            zoom_dir_path = os.path.join(dir_path, "zoom")
            if os.path.isdir(zoom_dir_path):
                for f in os.listdir(zoom_dir_path):
                    p = os.path.join(zoom_dir_path, f)
                    if os.path.isfile(p) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        slot = 2
                        slot_m = re.search(r'[-_](\d+)\.[a-zA-Z]+$', f)
                        if slot_m:
                            slot = int(slot_m.group(1))
                        processed_slots[slot] = p
                        
        # 2. Overlay TEST TOPAZ (2nd priority)
        if prod_norm in topaz_files:
            for slot, path in topaz_files[prod_norm]:
                processed_slots[slot] = path
                
        # 3. Overlay Refoma white background fix (1st priority)
        found_wb_fix_dir = None
        if prod_norm in wb_fix_folders:
            found_wb_fix_dir = wb_fix_folders[prod_norm]
        else:
            for f_norm, d_path in wb_fix_folders.items():
                if prod_norm == f_norm or prod_norm in f_norm or f_norm in prod_norm:
                    found_wb_fix_dir = d_path
                    break
        if found_wb_fix_dir:
            files = [f for f in os.listdir(found_wb_fix_dir) if os.path.isfile(os.path.join(found_wb_fix_dir, f))]
            processed_renders = [f for f in files if is_processed_render(f)]
            slots_candidates = {}
            for f in processed_renders:
                slot = extract_slot_from_filename(f)
                if slot is not None:
                    if slot not in slots_candidates:
                        slots_candidates[slot] = []
                    slots_candidates[slot].append(f)
            for slot, candidates in slots_candidates.items():
                best_cand = candidates[0]
                best_score = -1
                for cand in candidates:
                    cand_lower = cand.lower()
                    score = 0
                    if cand_lower.endswith(('.jpg', '.jpeg')) and ('-w-' in cand_lower or '-w.' in cand_lower or cand_lower.endswith(('-w.jpg', '-w.jpeg', '-w-wonder.jpg', '-w-wonder.jpeg', '-wonder-w.jpg', '-wonder-w.jpeg'))):
                        score = 10
                    elif cand_lower.endswith('.webp'):
                        score = 5
                    elif 'wonder' in cand_lower:
                        score = 4
                    if score > best_score:
                        best_score = score
                        best_cand = cand
                processed_slots[slot] = os.path.join(found_wb_fix_dir, best_cand)

        if not processed_slots:
            print(f"  ❌ Skipped: Could not find any images in any source folder for '{prod_name}'")
            skipped_count += 1
            continue
            
        # Sizing and classification
        category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
        target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
        print(f"  Category: {category} | Target W: {target_w:.3f} | Target H: {target_h:.3f} | Centered: {is_centered} | Floor: {floor_pct:.3f}")
        
        # Pinned perspective scale factor for the current SKU
        sku_scale = None
        sorted_slots = sorted(processed_slots.keys())
        main_slot_num = 1 if 1 in processed_slots else min(sorted_slots)

        for slot in sorted_slots:
            img_path = processed_slots[slot]
            is_main = (slot == main_slot_num)
            print(f"  --- Processing Slot {slot} (Main={is_main}) ---")
            
            # 1. Classification (Studio vs Lifestyle)
            is_studio = False
            if category == "lamp_pendant":
                print("    Classified as lamp_pendant. Bypassing cutout to preserve cables.")
                is_studio = False
            else:
                img_type = classify_image_type_robust(img_path, gemini_key)
                is_studio = (img_type == "studio")
                print(f"    Classified image type: {img_type.upper()}")
                
            normal_dest = os.path.join(artiklar_dir, f"{sku_clean}.jpg")
            liten_dest = os.path.join(liten_dir, f"{sku_clean}_S.jpg")
            zoom_dest = os.path.join(zoom_dir, f"{sku_clean}_{slot}.jpg" if not is_main else f"{sku_clean}_1.jpg")
            
            if is_dry_run:
                print(f"    [DRY-RUN] Processed successfully. Destination: {zoom_dest}")
                continue

            # Route 1: Lifestyle (no crop, copy as-is)
            if not is_studio:
                print("    Copying lifestyle image untouched...")
                try:
                    img_raw = Image.open(img_path)
                    img_resized = load_and_ensure_size(img_raw)
                    if is_main:
                        save_as_jpg(img_resized, normal_dest, 1000, quality=90)
                        save_as_jpg(img_resized, liten_dest, 400, quality=85)
                    save_as_jpg(img_resized, zoom_dest, 2000, quality=92)
                    img_resized.close()
                    img_raw.close()
                except Exception as e:
                    print(f"    Error copying lifestyle image: {e}")
                continue

            # Route 2: Studio (Preserve Natural Shadow + Clean Off-white Background + Auto-scale)
            final_canvas = None
            try:
                img_raw = Image.open(img_path)
                w, h = img_raw.size
                
                # 1. Resize keeping aspect ratio so longest side is 2000 (standardization step)
                longest = max(w, h)
                scale_init = 2000.0 / longest
                new_w = int(w * scale_init)
                new_h = int(h * scale_init)
                img_resized = img_raw.resize((new_w, new_h), RESAMPLING_METHOD)
                
                # 2. Check if background is off-white (studio) and needs cleaning
                img_rgb = img_resized.convert('RGB')
                arr = np.array(img_rgb)
                patches = [arr[10:25, 10:25], arr[10:25, -25:-10], arr[-25:-10, 10:25], arr[-25:-10, -25:-10]]
                means = [np.mean(pat, axis=(0,1)) for pat in patches]
                means.sort(key=lambda c: np.sum(c))
                bg_color = np.mean(means[1:], axis=0)
                bg_mean = np.mean(bg_color)
                grays = [0.299*m[0] + 0.587*m[1] + 0.114*m[2] for m in means[1:]]
                std_dev = np.std(grays)
                
                # We clean background if it's studio and close to white/light grey
                is_wb = (bg_mean > 200) and (std_dev < 20.0)
                
                if is_wb:
                    print(f"    Cleaning off-white background (detected bg: {bg_color.round(1)})...")
                    img_cleaned = clean_offwhite_background(img_resized, bg_color)
                else:
                    img_cleaned = img_resized
                    
                # Run SAM3 to get product body mask and restore light-colored product pixels
                bbox_clean = None
                if predictor is not None:
                    try:
                        print("    Running SAM3 body detection on CUDA to protect product pixels...")
                        text_prompts = get_sam3_text_prompt(category, prod_name)
                        with torch.no_grad():
                            results = predictor(img_resized, text=text_prompts)
                        if len(results) > 0 and results[0].masks is not None:
                            masks_tensor = results[0].masks.data
                            combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy()
                            combined_mask[:15, :] = False
                            combined_mask[-15:, :] = False
                            combined_mask[:, :15] = False
                            combined_mask[:, -15:] = False
                            coords_body = np.argwhere(combined_mask > 0)
                            if coords_body.size > 0:
                                y_min_clean = coords_body[:, 0].min()
                                y_max_clean = coords_body[:, 0].max()
                                x_min_clean = coords_body[:, 1].min()
                                x_max_clean = coords_body[:, 1].max()
                                bbox_clean = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
                                print(f"    SAM3 body bbox: x_min={x_min_clean}, y_min={y_min_clean}, x_max={x_max_clean}, y_max={y_max_clean}")
                                
                                # Restore original product pixels inside the body mask!
                                mask_pil = Image.fromarray((combined_mask * 255).astype(np.uint8), mode='L')
                                img_cleaned = Image.composite(img_resized, img_cleaned, mask_pil)
                                print("      Product pixels restored successfully via SAM3 mask.")
                    except Exception as e:
                        print(f"    Warning: SAM3 body detection/restore failed: {e}")
                        
                # 3. Check if this is a zoom/detail slot
                is_zoom_view = False
                fn_lower = os.path.basename(img_path).lower()
                zoom_keywords = ["zoom", "close", "detail", "skiss", "dimension", "material", "fabric", "leg", "tyg", "skrot", "narbete"]
                if any(kw in fn_lower for kw in zoom_keywords):
                    is_zoom_view = True
                elif slot is not None and slot >= 7:
                    if gemini_key:
                        print(f"    Slot {slot} >= 7. Querying Gemini to check zoom/detail status...")
                        is_zoom_view = query_gemini_for_zoom_status(img_path, gemini_key)
                    else:
                        is_zoom_view = True
                
                if is_zoom_view:
                    print("    Processing as ZOOM/DETAIL view (without tight cropping)...")
                    w_c, h_c = img_cleaned.size
                    longest_c = max(w_c, h_c)
                    scale_c = 1800.0 / longest_c
                    new_w_c = int(w_c * scale_c)
                    new_h_c = int(h_c * scale_c)
                    img_zoom_resized = img_cleaned.resize((new_w_c, new_h_c), RESAMPLING_METHOD)
                    
                    final_canvas = Image.new("RGB", (2000, 2000), (255, 255, 255))
                    paste_x = (2000 - new_w_c) // 2
                    paste_y = (2000 - new_h_c) // 2
                    final_canvas.paste(img_zoom_resized, (paste_x, paste_y))
                    img_zoom_resized.close()
                    print("    Zoom view centered and scaled to 90% successfully without tight cropping.")
                else:
                    # Find overall non-white region (product + shadow)
                    arr_cleaned = np.array(img_cleaned.convert('RGB'))
                    non_white = np.any(arr_cleaned < 254, axis=-1)
                    non_white[:5, :] = False
                    non_white[-5:, :] = False
                    non_white[:, :5] = False
                    non_white[:, -5:] = False
                    
                    coords_shadow = np.argwhere(non_white)
                    if coords_shadow.size > 0:
                        y_min_raw = coords_shadow[:, 0].min()
                        y_max_raw = coords_shadow[:, 0].max()
                        x_min_raw = coords_shadow[:, 1].min()
                        x_max_raw = coords_shadow[:, 1].max()
                        
                        # Fallback if SAM3 didn't run or failed
                        if bbox_clean is None:
                            print("    Falling back to threshold-based body bounding box...")
                            bbox_clean = (x_min_raw, y_min_raw, x_max_raw, y_max_raw)
                            
                        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
                        
                        crop_x_min = max(0, x_min_raw - 40)
                        crop_y_min = max(0, y_min_raw - 20)
                        crop_x_max = min(new_w, x_max_raw + 40)
                        crop_y_max = min(new_h, y_max_raw + 20)
                        
                        cropped = img_cleaned.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
                        W_p = x_max_clean - x_min_clean
                        H_p = y_max_clean - y_min_clean
                        
                        # Calculate scale factor
                        if is_main or (sku_scale is None):
                            scale_w = (target_w * 2000.0) / W_p
                            scale_h = (target_h * 2000.0) / H_p
                            scale = min(scale_w, scale_h)
                            if is_main:
                                sku_scale = scale
                                print(f"    [Perspective Scale] Main slot set scale factor: {sku_scale:.6f}")
                        else:
                            scale = sku_scale
                            print(f"    [Perspective Scale] Reusing main slot scale factor: {sku_scale:.6f}")
                            
                        # Apply safety limits
                        if W_p * scale > 1900.0:
                            print(f"    Applying safety width limit: scaled width {W_p * scale:.1f} exceeds 1900. Capping scale.")
                            scale = 1900.0 / W_p
                            
                        if is_centered:
                            if H_p * scale > 1900.0:
                                scale = 1900.0 / H_p
                        else:
                            max_h_allowed = int(2000 - (floor_pct * 2000) - 50)
                            if H_p * scale > max_h_allowed:
                                print(f"    Applying safety height limit: scaled height {H_p * scale:.1f} exceeds max allowed {max_h_allowed}. Capping scale.")
                                scale = max_h_allowed / H_p
                            
                        new_w_body = int(W_p * scale)
                        new_h_body = int(H_p * scale)
                        
                        # Scale the entire cropped region (containing natural shadow)
                        new_w_crop = int((crop_x_max - crop_x_min) * scale)
                        new_h_crop = int((crop_y_max - crop_y_min) * scale)
                        cropped_resized = cropped.resize((new_w_crop, new_h_crop), RESAMPLING_METHOD)
                        
                        final_canvas = Image.new("RGB", (2000, 2000), (255, 255, 255))
                        paste_x_body = (2000 - new_w_body) // 2
                        
                        if is_centered:
                            paste_y_body = (2000 - new_h_body) // 2
                        else:
                            paste_y_body = int(2000 - (floor_pct * 2000) - new_h_body)
                            
                        # Calculate relative paste coordinates for the full crop
                        offset_x = x_min_clean - crop_x_min
                        offset_y = y_min_clean - crop_y_min
                        
                        paste_x = paste_x_body - int(offset_x * scale)
                        paste_y = paste_y_body - int(offset_y * scale)
                        
                        final_canvas.paste(cropped_resized, (paste_x, paste_y))
                        cropped.close()
                        cropped_resized.close()
                        print("    Off-white background cleaned, body-centered, and auto-scaled successfully.")
                    else:
                        # Fallback if no bounding box found
                        final_canvas = Image.new("RGB", (2000, 2000), (255, 255, 255))
                        paste_x = (2000 - new_w) // 2
                        paste_y = (2000 - new_h) // 2
                        final_canvas.paste(img_cleaned, (paste_x, paste_y))
                        print("    Warning: No product pixels found, pasted centered as fallback.")
                
                img_raw.close()
                if img_resized != img_cleaned:
                    img_cleaned.close()
                img_resized.close()
            except Exception as e:
                print(f"    Error processing studio image background clean and scale: {e}")
                final_canvas = None

            # Save outputs
            if final_canvas is not None:
                if is_main:
                    save_as_jpg(final_canvas, normal_dest, 1000, quality=90)
                    save_as_jpg(final_canvas, liten_dest, 400, quality=85)
                save_as_jpg(final_canvas, zoom_dest, 2000, quality=92)
                print(f"    Successfully saved outputs for slot {slot}.")
                try:
                    final_canvas.close()
                except Exception:
                    pass
                final_canvas = None
            
            # Clean up temp file
            if temp_output_path.exists():
                try:
                    os.remove(temp_output_path)
                except Exception:
                    pass

        processed_count += 1
        
    print("\n==================================================")
    print("      COMFYUI COGNITIVE PIPELINE COMPLETED        ")
    print("==================================================")
    print(f"✓ Processed {processed_count} products.")
    print(f"✗ Skipped {skipped_count} products (no images found).")
    print("==================================================")

if __name__ == "__main__":
    main()
