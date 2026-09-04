import os
import re
import sys
import json
import base64
import time
import requests
import numpy as np
from PIL import Image
from io import BytesIO
from reforma_pipeline.config import CATEGORY_TARGETS, GEMINI_ENV_PATH

def post_gemini_request_with_retry(url, headers, json_data, timeout=20, max_retries=5):
    delay = 2.0
    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            if res.status_code == 429:
                try:
                    err_msg = res.json().get("error", {}).get("message", "").lower()
                    if "spending cap" in err_msg or "spend cap" in err_msg:
                        print("  [Classifier Error] Gemini spending cap exceeded. Skipping retries.")
                        return res
                except Exception:
                    pass
                print(f"  [Classifier Warning] Gemini rate limit hit (429). Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2.0
                continue
            res.raise_for_status()
            return res
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                try:
                    err_msg = e.response.json().get("error", {}).get("message", "").lower()
                    if "spending cap" in err_msg or "spend cap" in err_msg:
                        print("  [Classifier Error] Gemini spending cap exceeded. Skipping retries.")
                        return e.response
                except Exception:
                    pass
                print(f"  [Classifier Warning] Gemini rate limit hit (429). Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2.0
                continue
            time.sleep(1.0)
    raise RuntimeError("Max retries exceeded for Gemini API request")

def query_gemini_batch_for_sku(sku, slots_data, gemini_key):
    sorted_slots = sorted(slots_data.keys())
    parts = []
    prompt = (
        "You are an expert product image classifier. We have a set of images for a single furniture product SKU. "
        "The images are labeled sequentially: Image_1, Image_2, etc.\n"
        "Analyze each image and classify it into:\n"
        "1. image_type: 'studio' (product isolated on white/light backdrop), "
        "'lifestyle' (product staged in a room environment), or "
        "'detail' (close-up of fabric, joints, legs, or a technical drawing/sketch/blueprint with dimensions/text).\n"
        "2. has_white_bg: true if the background is a plain white/off-white studio backdrop, otherwise false.\n"
        "3. is_zoom_or_detail: true if the image is a close-up/detail shot or a technical drawing/sketch, "
        "and false if it shows the entire standalone product.\n\n"
        "Reply strictly in JSON format matching this schema:\n"
        "{\n"
        "  \"Image_1\": {\"image_type\": \"studio\"|\"lifestyle\"|\"detail\", \"has_white_bg\": true|false, \"is_zoom_or_detail\": true|false},\n"
        "  \"Image_2\": ...\n"
        "}"
    )
    parts.append({"text": prompt})
    
    idx_to_slot = {}
    for idx, slot in enumerate(sorted_slots):
        img_path = slots_data[slot]
        try:
            with Image.open(img_path) as img:
                img_resized = img.resize((500, 500))
                buffered = BytesIO()
                img_resized.convert('RGB').save(buffered, format="JPEG", quality=80)
                img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            label = f"Image_{idx+1}"
            idx_to_slot[label] = slot
            parts.append({"text": f"--- {label} (Slot {slot}) ---"})
            parts.append({"inlineData": {"mimeType": "image/jpeg", "data": img_data}})
        except Exception as e:
            print(f"  [Classifier Warning] Failed to read/encode slot {slot} for batch: {e}")
            
    if len(parts) <= 1:
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    try:
        res = post_gemini_request_with_retry(url, headers, data, timeout=30)
        if res.status_code == 200:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            batch_result = json.loads(text_resp)
            
            mapped_result = {}
            for label, slot in idx_to_slot.items():
                res_item = batch_result.get(label)
                if res_item:
                    mapped_result[slot] = {
                        "image_type": res_item.get("image_type", "studio"),
                        "has_white_bg": res_item.get("has_white_bg", True),
                        "is_zoom_or_detail": res_item.get("is_zoom_or_detail", False)
                    }
            return mapped_result
    except Exception as e:
        print(f"  [Classifier Warning] Batch Gemini classification failed: {e}")
    return None

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
    name = name.lower()
    # Map Swedish and accented characters to their standard equivalent
    replacements = {
        'å': 'a', 'ä': 'a', 'ö': 'o', 'é': 'e', 'è': 'e',
        'ü': 'u', 'ó': 'o', 'á': 'a', 'í': 'i', 'ø': 'o', 'æ': 'a'
    }
    for char, rep in replacements.items():
        name = name.replace(char, rep)
    return re.sub(r'[^a-z0-9]', '', name)

def classify_and_size_product(folder_name):
    folder_lower = folder_name.lower()
    
    # SOFA
    is_sofa = False
    if any(x in folder_lower for x in ["soffa", "sofa", "baddsoffa", "bäddsoffa", "schaslong"]):
        is_sofa = True
    if is_sofa:
        is_2_seat = any(x in folder_lower for x in ["2-sits", "2-seater", "2sits", "2seater", "loveseat", "love-seat", "baddfatolj", "bäddfåtölj"])
        cat = "sofa_2_seat" if is_2_seat else "sofa_3_seat"
        cfg = CATEGORY_TARGETS[cat]
        return cat, cfg["target_w"], cfg["target_h"], cfg["floor_pct"], cfg["is_centered"]

    # CHAIRS, ARMCHAIRS, BARSTOOLS, STOOLS
    is_chair = any(x in folder_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "chair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"])
    if is_chair:
        if any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol"]):
            cat = "armchair"
        elif "barstol" in folder_lower:
            cat = "barstool"
        elif any(x in folder_lower for x in ["pall", "puff", "sittpuff"]):
            cat = "stool"
        else:
            cat = "chair_dining"
        cfg = CATEGORY_TARGETS[cat]
        return cat, cfg["target_w"], cfg["target_h"], cfg["floor_pct"], cfg["is_centered"]

    # TABLES
    is_table = any(x in folder_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord", "table", "desk"])
    if is_table:
        is_dining = any(x in folder_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"])
        cat = "table_large" if is_dining else "table_small"
        cfg = CATEGORY_TARGETS[cat]
        return cat, cfg["target_w"], cfg["target_h"], cfg["floor_pct"], cfg["is_centered"]

    # CABINETS
    is_cabinet = any(x in folder_lower for x in ["skap", "skåp", "byra", "byrå", "sideboard", "skank", "skänk", "garderob", "tv-bank", "tv-bänk", "vinhylla", "cabinet", "cupboard", "wardrobe", "dresser", "kladhangare", "klädhängare", "kladstall", "klädställ"])
    if is_cabinet:
        is_large = any(x in folder_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ"]) or ("skap" in folder_lower or "skåp" in folder_lower) and not any(x in folder_lower for x in ["sido", "litet", "byra", "byrå"])
        cat = "cabinet_large" if is_large else "cabinet_small"
        cfg = CATEGORY_TARGETS[cat]
        return cat, cfg["target_w"], cfg["target_h"], cfg["floor_pct"], cfg["is_centered"]

    # SHELVES
    is_shelf = any(x in folder_lower for x in ["hylla", "hyllor", "vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "shelf", "shelves", "bookcase"])
    if is_shelf:
        is_wall = any(x in folder_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"])
        cat = "shelf_hanging" if is_wall else "shelf_floor"
        cfg = CATEGORY_TARGETS[cat]
        return cat, cfg["target_w"], cfg["target_h"], cfg["floor_pct"], cfg["is_centered"]

    # LIGHTING
    is_lamp = any(x in folder_lower for x in ["lamp", "lampa", "belysning", "ljus", "stjarna", "stjärna", "advent", "ceiling", "pendant", "chandelier", "suspension", "hanging", "light", "fixture", "bulb", "krona", "plafond"])
    if is_lamp:
        if any(x in folder_lower for x in ["golv", "floor"]):
            cat = "lamp_floor"
        elif any(x in folder_lower for x in ["bord", "table", "desk"]):
            cat = "lamp_table"
        elif any(x in folder_lower for x in ["taklampa", "pendel", "krona", "plafond", "adventstjarna", "adventstjärna", "stjarna", "stjärna", "oslo", "sally", "lotus", "ceiling", "pendant", "chandelier", "suspension", "hanging", "semi", "multi-lite", "gubi"]):
            cat = "lamp_pendant"
        elif any(x in folder_lower for x in ["vagg", "vägg", "wall", "sconce"]):
            cat = "lamp_wall"
        else:
            cat = "lamp_pendant"
        cfg = CATEGORY_TARGETS[cat]
        return cat, cfg["target_w"], cfg["target_h"], cfg["floor_pct"], cfg["is_centered"]


    # DEFAULT
    cfg = CATEGORY_TARGETS["default"]
    return "default", cfg["target_w"], cfg["target_h"], cfg["floor_pct"], cfg["is_centered"]

def adjust_size_by_name(category, name, target_w, target_h):
    name_lower = name.lower()
    
    # 1. Sofas (e.g., Luleå, Lionel, etc.)
    if "lule" in name_lower or "luleå" in name_lower:
        if "3" in name_lower or "härnösand" in name_lower:
            target_w = 0.94
        else:
            target_w = 0.91
            
    # 2. Dining Tables
    if category == "table_large":
        if "180" in name_lower or "200" in name_lower or "220" in name_lower:
            target_w = 0.94
        elif "140" in name_lower or "120" in name_lower:
            target_w = 0.88
            
    # 3. Wardrobes/Large cabinets height override
    if category == "cabinet_large":
        m_cross = re.search(r'(\d+)x(\d+)', name_lower)
        numbers = re.findall(r'\b\d+\b', name_lower)
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
        res = post_gemini_request_with_retry(url, headers, data, timeout=20)
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
        res = post_gemini_request_with_retry(url, headers, data, timeout=20)
        if res.status_code == 200:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            classification = json.loads(text_resp)
            return classification.get("is_zoom_or_detail", False)
    except Exception as e:
        print(f"  [Classifier Warning] Gemini zoom classification failed: {e}")
    return None

def resolve_zoom_status(img_path, img_key, gemini_key, cache=None,
                        load_cache_func=None, save_cache_func=None):
    """
    Centralized, cached resolver for the 'is this a zoom/detail view?' question.

    Queries Gemini at most ONCE per image (keyed by img_key) and reuses the verdict
    everywhere — curation, the Stage 3 override and the Stage 4 audit. Persisting the
    answer the first time it is known is what breaks the Stage-1/Stage-2 catch-22
    ("need a bbox to decide zoom, need non-zoom to make a bbox").

    Pass an in-memory `cache` dict and/or `load_cache_func`/`save_cache_func` for
    process-safe persistence (the CPU pool re-reads the latest cache before writing).
    Returns True/False, or None if the status is genuinely unknown (no key / API down).
    """
    cache_key = f"zoom_{img_key}"

    # 1. In-memory hit
    if cache is not None and cache_key in cache:
        return cache[cache_key]

    # 2. Persistent hit (re-read latest to stay correct across parallel workers)
    if load_cache_func is not None:
        try:
            latest = load_cache_func()
        except Exception:
            latest = {}
        if cache_key in latest:
            if cache is not None:
                cache[cache_key] = latest[cache_key]
            return latest[cache_key]

    # 3. Resolve via Gemini (once) and persist
    if not gemini_key:
        return None
    res = query_gemini_for_zoom_status(img_path, gemini_key)
    if res is None:
        return None
    if cache is not None:
        cache[cache_key] = res
    if load_cache_func is not None and save_cache_func is not None:
        try:
            latest = load_cache_func()
            latest[cache_key] = res
            save_cache_func(latest)
        except Exception as e:
            print(f"  [Classifier Warning] Failed to persist zoom cache for {img_key}: {e}")
    return res

def query_gemini_for_visual_semantics(img_path, key):
    try:
        with Image.open(img_path) as img:
            img_resized = img.resize((500, 500))
            buffered = BytesIO()
            img_resized.convert('RGB').save(buffered, format="JPEG", quality=80)
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        prompt = (
            "Analyze this product image and determine:\n"
            "1. image_type: Choose 'studio' (product isolated on a studio backdrop), "
            "'lifestyle' (product staged inside a realistic room/miljö scene), or "
            "'detail' (close-up/zoom of fabric, joints, wood grain, or stitching).\n"
            "2. has_white_bg: Choose true if the background is a plain white/off-white studio backdrop, "
            "otherwise false (if it is a room environment, textured panel, or colored surface).\n\n"
            "Reply strictly in JSON format:\n"
            "{\n"
            "  \"image_type\": \"studio\" | \"lifestyle\" | \"detail\",\n"
            "  \"has_white_bg\": true | false\n"
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
        res = post_gemini_request_with_retry(url, headers, data, timeout=20)
        if res.status_code == 200:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            classification = json.loads(text_resp)
            return {
                "image_type": classification.get("image_type", "studio"),
                "has_white_bg": classification.get("has_white_bg", True)
            }
    except Exception as e:
        print(f"  [Classifier Warning] Gemini visual semantics query failed: {e}")
    return None

def classify_image_semantics_robust(img_path, gemini_key=None):
    if gemini_key:
        print(f"  [Classifier] Querying Gemini for semantics: {os.path.basename(img_path)}")
        res = query_gemini_for_visual_semantics(img_path, gemini_key)
        if res is not None:
            return res
        print("  [Classifier Warning] Gemini semantics query failed. Falling back to local heuristics.")
        
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
        
        has_white_bg = False
        image_type = "lifestyle"
        
        if white_pixel_ratio > 0.30 and mean_sat < 0.08:
            has_white_bg = True
            image_type = "studio"
        elif mean_luma > 0.94 and std_luma < 0.10 and mean_sat < 0.06:
            has_white_bg = True
            image_type = "studio"
        elif mean_luma > 0.88 and mean_sat < 0.10:
            has_white_bg = True
            image_type = "studio"
            
        return {
            "image_type": image_type,
            "has_white_bg": has_white_bg
        }
    except Exception as e:
        print(f"  [Classifier Error] Heuristic semantics classification failed: {e}")
        return {"image_type": "studio", "has_white_bg": True}

def classify_image_type_robust(img_path, gemini_key=None):
    semantics = classify_image_semantics_robust(img_path, gemini_key)
    t = semantics["image_type"]
    if t == "studio":
        return "studio"
    elif t == "detail":
        return "studio" if semantics["has_white_bg"] else "lifestyle"
    else:
        return "lifestyle"

def is_zoom_or_sketch(img_path, img_type, slot, img_key, cache, gemini_key=None, bbox_db=None, main_slot_num=1):
    fn_lower = os.path.basename(img_path).lower()
    zoom_keywords = ["zoom", "close", "detail", "skiss", "dimension", "material", "fabric", "leg", "tyg", "skrot", "narbete", "blueprint", "drawing"]
    if any(kw in fn_lower for kw in zoom_keywords):
        return True
    if img_type == "detail":
        return True
        
    # Local line-drawing/sketch detection heuristic
    is_sketch_candidate = False
    try:
        with Image.open(img_path) as img_sketch:
            resample_method = getattr(Image, 'Resampling', Image).NEAREST
            img_sketch_small = img_sketch.resize((100, 100), resample_method).convert('RGB')
            arr_sketch = np.array(img_sketch_small, dtype=np.float32)
            r = arr_sketch[:, :, 0]
            g = arr_sketch[:, :, 1]
            b = arr_sketch[:, :, 2]
            luma = 0.299 * r + 0.587 * g + 0.114 * b
            
            pct_bg = np.sum(luma >= 235) / luma.size
            diff_rg = np.mean(np.abs(r - g))
            diff_gb = np.mean(np.abs(g - b))
            
            if pct_bg >= 0.88 and diff_rg < 8.0 and diff_gb < 8.0:
                is_sketch_candidate = True
            img_sketch_small.close()
    except Exception as e:
        print(f"  [Classifier Warning] Sketch heuristic failed for {os.path.basename(img_path)}: {e}")
        
    # Skip margin touch heuristics for main slot (we never want to class slot 1 as zoom view)
    skip_margin_touch_heuristics = (slot == main_slot_num)


    # Check bbox database for margin touches if available
    is_margin_touch_candidate = False
    if not skip_margin_touch_heuristics and bbox_db and img_key in bbox_db:
        new_w, new_h = 2000, 2000
        try:
            with Image.open(img_path) as img_temp:
                w_orig, h_orig = img_temp.size
                longest = max(w_orig, h_orig)
                scale_init = 2000.0 / longest
                new_w = int(w_orig * scale_init)
                new_h = int(h_orig * scale_init)
        except Exception:
            pass

        bbox_clean = bbox_db[img_key]
        x_min, y_min, x_max, y_max = bbox_clean
        bbox_w = x_max - x_min
        bbox_h = y_max - y_min
        touches_left = (x_min <= 25)
        touches_right = (x_max >= new_w - 25)
        touches_top = (y_min <= 25)
        touches_bottom = (y_max >= new_h - 25)
        
        touches_sides = (touches_left and touches_right)
        touches_tb = (touches_top and touches_bottom)
        is_large_closeup = (bbox_w >= int(new_w * 0.85)) or (bbox_h >= int(new_h * 0.85))
        
        # If it touches 3 or more margins, it is unconditionally a zoom view
        num_touches = sum([touches_left, touches_right, touches_top, touches_bottom])
        if num_touches >= 3:
            return True
            
        # If it touches top, left, or right margins, it is unconditionally a zoom/detail view.
        # Studio views always have white padding around the product body on the sides and top.
        if touches_top or touches_left or touches_right:
            return True
            
        # If it touches the bottom margin and has a huge empty space at the top,
        # it is a close-up of the legs/seat (missing backrest).
        if touches_bottom and (y_min >= 400):
            return True
            
        if is_large_closeup or touches_sides or touches_tb:
            is_margin_touch_candidate = True

    # If sketch or margin-touch triggers, confirm via the cached zoom-status helper
    # (queries Gemini at most once per image and stores the verdict in the cache).
    if is_sketch_candidate or is_margin_touch_candidate:
        res = resolve_zoom_status(img_path, img_key, gemini_key, cache=cache)
        return bool(res) if res is not None else False

    return False

