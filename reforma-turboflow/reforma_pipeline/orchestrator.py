import os
import re
import sys
import json
import gc
import shutil
import numpy as np
from PIL import Image
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Set up encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import modules from package
from reforma_pipeline.config import (
    CANVAS_SIZE, BRAND_DICT_PATH, NEW_WHITE_BG_DIR, TOPAZ_DIR, ORIG_DIR, FTP_UPLOAD_DIR,
    CATEGORY_TARGETS
)
from reforma_pipeline.classification import (
    load_gemini_key, normalize_name, classify_and_size_product, adjust_size_by_name,
    classify_image_type_robust, query_gemini_for_zoom_status, classify_image_semantics_robust,
    is_zoom_or_sketch, query_gemini_batch_for_sku, resolve_zoom_status
)
from reforma_pipeline.decolorization import clean_offwhite_background
from reforma_pipeline.composition import CompositionEngine
from reforma_pipeline.qa_loop import IterativeQACoordinator
from reforma_pipeline.local_vlm import query_florence2_bbox, unload_florence2_model



script_dir = os.path.dirname(os.path.abspath(__file__))
turboflow_dir = os.path.dirname(script_dir)
CACHE_PATH = os.path.join(turboflow_dir, "scratch", "classification_cache.json")
BBOX_DB_PATH = os.path.join(turboflow_dir, "scratch", "bbox_coordinates_db.json")

# Helper for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

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

def get_file_sig(path):
    try:
        return f"{os.path.getsize(path)}_{int(os.path.getmtime(path))}"
    except Exception:
        return "nosig"

import time
def save_image_safe(pil_img, dest_path, quality=90, format="JPEG"):
    """
    Saves PIL image to dest_path, handling Windows/OneDrive file locking gracefully
    using atomic temporary file replacement, force-deletion, and retries.
    """
    temp_dest = dest_path + ".tmp"
    max_retries = 5
    
    # 1. Save to a temporary file first
    for attempt in range(max_retries):
        try:
            os.makedirs(os.path.dirname(temp_dest), exist_ok=True)
            if os.path.exists(temp_dest):
                try: os.remove(temp_dest)
                except Exception: pass
            pil_img.save(temp_dest, format, quality=quality)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise IOError(f"Failed to write temporary file {temp_dest}: {e}")
            time.sleep(0.1)
            
    # 2. Atomic replacement: delete existing and rename temp to dest
    for attempt in range(max_retries):
        try:
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except Exception:
                    # If delete fails, try renaming to junk first (classic Windows lock bypass)
                    junk_path = dest_path + f".junk_{int(time.time())}"
                    if os.path.exists(junk_path):
                        try: os.remove(junk_path)
                        except Exception: pass
                    os.rename(dest_path, junk_path)
                    try: os.remove(junk_path)
                    except Exception: pass
            os.rename(temp_dest, dest_path)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                # Final fallback: direct save
                try:
                    pil_img.save(dest_path, format, quality=quality)
                    return
                except Exception as final_err:
                    raise IOError(f"Failed to overwrite destination {dest_path} after retries: {final_err}")
            time.sleep(0.2)

def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(cache):
    os.makedirs("scratch", exist_ok=True)
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def load_bbox_db():
    if os.path.exists(BBOX_DB_PATH):
        try:
            with open(BBOX_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_bbox_db(db):
    os.makedirs("scratch", exist_ok=True)
    with open(BBOX_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2)

def estimate_scale_from_composed(img_path, composed_path, bbox_clean):
    if not bbox_clean:
        return None
    try:
        _, y_min_orig, _, y_max_orig = bbox_clean
        h_orig = y_max_orig - y_min_orig
        if h_orig <= 0:
            return None
        with Image.open(composed_path) as comp_img:
            arr = np.array(comp_img.convert('RGB'))
            diff = np.sum(255 - arr, axis=-1)
            non_white = diff > 15
            # Ignore borders
            non_white[:15, :] = False
            non_white[-15:, :] = False
            non_white[:, :15] = False
            non_white[:, -15:] = False
            coords = np.argwhere(non_white)
            if coords.size == 0:
                return None
            y_min_comp = coords[:, 0].min()
            y_max_comp = coords[:, 0].max()
            h_comp = y_max_comp - y_min_comp
            return float(h_comp) / float(h_orig)
    except Exception as e:
        print(f"  [Scale Estimator Warning] Failed to estimate scale: {e}")
    return None

# Helper function to process a single SKU in CPU phase
def process_sku_cpu_worker(sku_data):

    prod_name, info, processed_slots, _, artiklar_dir, liten_dir, zoom_dir = sku_data
    # Force loading the most up-to-date bbox database from disk to avoid Windows multiprocessing synchronization lag
    bbox_data = load_bbox_db()
    sku = info['sku'].strip()
    
    category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
    target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
    
    engine = CompositionEngine()
    qa_coordinator = IterativeQACoordinator()

    sorted_slots = sorted(processed_slots.keys())
    main_slot_num = 1 if 1 in processed_slots else min(sorted_slots)
    
    # We will track the scale factor dynamically
    sku_scale = None
    results = []
    
    for slot in sorted_slots:
        img_info = processed_slots[slot]
        img_path = img_info['path']
        is_studio = img_info['is_studio']
        is_zoom_view = img_info['is_zoom_view']
        has_white_bg = img_info.get('has_white_bg', True)
        is_main = (slot == main_slot_num)
        
        # Recover SAM3 body bbox (precalculated during Stage 2)
        bbox_clean = None
        img_key = img_info.get('img_key', f"{sku}_{slot}")
        if img_key in bbox_data:
            bbox_clean = bbox_data[img_key]
        elif is_studio:
            # No SAM3 bbox (e.g. GPU unavailable). Resolve zoom/detail status via the
            # cached helper so a close-up is not mis-composed as a full studio view.
            # This is the no-bbox arm that breaks the curation zoom catch-22 when Stage 2
            # produced nothing.
            res = resolve_zoom_status(
                img_path, img_key, load_gemini_key(),
                load_cache_func=load_cache, save_cache_func=save_cache
            )
            is_zoom_view = is_zoom_view or bool(res)
            
        # Heuristic override: if the bounding box is extremely large (occupies >= 85% of canvas width or height)
        # or touches both sides, or touches top and bottom, or touches top/left/right margins,
        # it is a close-up detail/fabric shot and should bypass canvas grounding/centering QA checks
        skip_margin_touch_heuristics = (slot == main_slot_num)

        if bbox_clean is not None and not skip_margin_touch_heuristics:
            # Dynamically compute resized dimensions
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
            if is_large_closeup or touches_sides or touches_tb or touches_top or touches_left or touches_right:
                # Authoritative Stage 3 zoom override: now that a SAM3 bbox exists we can
                # trust the margin-touch geometry. >=3 margin touches is unconditionally a
                # zoom; otherwise confirm once via the cached Gemini helper.
                num_touches = sum([touches_left, touches_right, touches_top, touches_bottom])
                if num_touches >= 3:
                    is_zoom_confirm = True
                else:
                    res = resolve_zoom_status(
                        img_path, img_key, load_gemini_key(),
                        load_cache_func=load_cache, save_cache_func=save_cache
                    )
                    is_zoom_confirm = bool(res)
                is_zoom_view = is_zoom_view or is_zoom_confirm
        
        normal_dest = os.path.join(artiklar_dir, f"{sku}.jpg")
        liten_dest = os.path.join(liten_dir, f"{sku}_S.jpg")
        zoom_dest = os.path.join(zoom_dir, f"{sku}_{slot}.jpg" if not is_main else f"{sku}_1.jpg")
        
        # Skip if existing zoom output is already square and it's a studio view (not zoom view)
        if not is_zoom_view and os.path.exists(zoom_dest):

            try:
                with Image.open(zoom_dest) as img_check:
                    w_c, h_c = img_check.size
                    if w_c == h_c:
                        print(f"  [Skipping Slot] SKU {sku} Slot {slot} zoom is already square ({w_c}x{h_c}). Skipping.")
                        results.append((slot, "skipped_already_square"))
                        
                        # Estimate scale factor if this is the main slot and not zoom, so subsequent slots can be scaled consistently
                        if is_main and not is_zoom_view:
                            estimated_scale = estimate_scale_from_composed(img_path, zoom_dest, bbox_clean)
                            if estimated_scale is not None:
                                sku_scale = estimated_scale
                                engine.scale_cache[sku] = estimated_scale
                                print(f"  [Skipping Slot] Estimated scale factor from existing square main image: {estimated_scale:.4f}")
                        continue
            except Exception as e:
                print(f"  [Skipping Slot Warning] Error checking existing square image for SKU {sku} Slot {slot}: {e}")

        
        # Route 1: Lifestyle / Close-up / Detail / Sketch / Zoom (no crop, copy as-is)
        # Route selection: ONLY a genuine white-background, non-zoom studio view is
        # eligible for the square hero crop (Route 2). Everything else — lifestyle,
        # any zoom/detail, and gray-background "studio" close-ups — stays here and is
        # NEVER force-padded onto a white canvas (the cause of the gray/white seam).
        if not (is_studio and has_white_bg) or is_zoom_view:
            try:
                with Image.open(img_path) as img_raw:
                    w, h = img_raw.size
                    scale_init = 2000.0 / max(w, h)
                    new_w = int(w * scale_init)
                    new_h = int(h * scale_init)
                    img_resized = img_raw.resize((new_w, new_h), RESAMPLING_METHOD)

                    # Pad to a 2000x2000 white square ONLY for a true white-background,
                    # non-zoom view (e.g. a white-bg sketch). Zoom views and ANY
                    # non-white background keep their natural rectangular format so the
                    # background stays continuous — no seam.
                    did_pad = has_white_bg and not is_zoom_view
                    if did_pad:
                        padded_img = Image.new("RGB", (2000, 2000), (255, 255, 255))
                        padded_img.paste(img_resized, ((2000 - new_w) // 2, (2000 - new_h) // 2))
                        img_to_save = padded_img
                    else:
                        img_to_save = img_resized

                    if is_main:
                        normal_img_temp = img_to_save.resize((1000, 1000) if did_pad else (1000, int(new_h * 1000 / new_w)), RESAMPLING_METHOD).convert('RGB')
                        save_image_safe(normal_img_temp, normal_dest, quality=90)
                        normal_img_temp.close()
                        liten_img_temp = img_to_save.resize((400, 400) if did_pad else (400, int(new_h * 400 / new_w)), RESAMPLING_METHOD).convert('RGB')
                        save_image_safe(liten_img_temp, liten_dest, quality=85)
                        liten_img_temp.close()

                    zoom_img_temp = img_to_save.convert('RGB')
                    save_image_safe(zoom_img_temp, zoom_dest, quality=92)
                    zoom_img_temp.close()

                    if did_pad:
                        padded_img.close()
                    img_resized.close()
                results.append((slot, "copied_lifestyle"))
            except Exception as e:
                results.append((slot, f"error_lifestyle: {e}"))
            continue
            
        # Route 2: Studio (Clean background + auto-scale)
        try:
            with Image.open(img_path) as img_raw:
                w, h = img_raw.size
                longest = max(w, h)
                scale_init = 2000.0 / longest
                new_w = int(w * scale_init)
                new_h = int(h * scale_init)
                img_resized = img_raw.resize((new_w, new_h), RESAMPLING_METHOD)
                
                # Check background white balance and clean if needed
                img_rgb = img_resized.convert('RGB')
                arr = np.array(img_rgb)
                patches = [arr[10:25, 10:25], arr[10:25, -25:-10], arr[-25:-10, 10:25], arr[-25:-10, -25:-10]]
                means = [np.mean(pat, axis=(0,1)) for pat in patches]
                means.sort(key=lambda c: np.sum(c))
                bg_color = np.mean(means[1:], axis=0)
                bg_mean = np.mean(bg_color)
                grays = [0.299*m[0] + 0.587*m[1] + 0.114*m[2] for m in means[1:]]
                std_dev = np.std(grays)
                is_wb = (bg_mean > 200) and (std_dev < 20.0)

                # FIX: the inverted guard silently re-enabled cleanup under FORCE_ORIGINAL and
                # desaturated the retouched shadow. The white-background-fix source must NEVER
                # be decolorized (preserve the pristine soft shadow). Off-white Topaz/original
                # sources are still normalized to white upstream, which the solid paste keeps.
                is_from_fix_folder = "refoma white background fix" in img_path.lower()
                if is_from_fix_folder:
                    is_wb = False

                # Load overrides to check for highlights adjustment
                overrides = qa_coordinator.load_overrides()
                sku_overrides = overrides.get(sku, {})
                slot_override = sku_overrides.get(str(slot), {})
                h_thresh = slot_override.get("highlight_threshold", None)
                h_fact = slot_override.get("highlight_factor", None)

                # Define lambda function to clean background using custom tolerance/blend_range
                # This allows the QA coordinator to adjust these params on the fly
                img_cleaned_func = lambda tol, blend: clean_offwhite_background(
                    img_resized, bg_color, tol, blend, highlight_threshold=h_thresh, highlight_factor=h_fact
                ) if is_wb else img_resized.copy()

                # Run QA and Corrective Loop
                final_canvas, scale_used, passed = qa_coordinator.run_qa_and_correct(
                    engine=engine,
                    img_cleaned_func=img_cleaned_func,
                    bbox_clean=bbox_clean,
                    category=category,
                    sku=sku,
                    slot=slot,
                    is_zoom_view=is_zoom_view,
                    bg_color=bg_color if is_wb else np.array([255.0, 255.0, 255.0]),
                    target_w=target_w,
                    target_h=target_h,
                    floor_pct=floor_pct,
                    is_centered=is_centered,
                    sku_scale=sku_scale if not is_zoom_view else None,
                    gemini_key=load_gemini_key(),
                    is_from_fix_folder=is_from_fix_folder,
                    allow_local_gpu_qa=False  # GPU-säkert: ingen lokal Florence-2 i CPU-poolen (Stage 3)
                )

                # Save the scale factor from the main view for subsequent hero slots
                if not is_zoom_view and is_main:
                    sku_scale = scale_used
                
                # Save outputs
                if is_main:
                    normal_img_temp = final_canvas.resize((1000, 1000), RESAMPLING_METHOD)
                    save_image_safe(normal_img_temp, normal_dest, quality=90)
                    normal_img_temp.close()
                    
                    liten_img_temp = final_canvas.resize((400, 400), RESAMPLING_METHOD)
                    save_image_safe(liten_img_temp, liten_dest, quality=85)
                    liten_img_temp.close()
                    
                    # If this main slot failed, we might also want to know which output file it is.
                    # We can keep track of it.
                    
                save_image_safe(final_canvas, zoom_dest, quality=92)
                
                # If failed, we write a special flag file or JSON file to help the wrapper script find the failed image
                if not passed:
                    is_raw_source = "reforma_original_images_by_product" in img_path.lower() or "test topaz" in img_path.lower()
                    if is_raw_source:
                        print(f"  [QA Fallback] SKU {sku} Slot {slot} failed studio QA. Keeping best-attempt canvas for raw source.")
                        # Keep best attempt final_canvas (do not fall back to Route 1 and do not raise failure)
                        passed = True
                    elif slot >= 2:
                        print(f"  [QA Fallback] SKU {sku} Slot {slot} failed studio QA. Falling back to zoom view (Route 1)...")
                        final_canvas.close()
                        
                        # Generate Route 1 zoom view
                        w_zoom, h_zoom = img_resized.size
                        longest = max(w_zoom, h_zoom)
                        scale_zoom = 2000.0 / longest
                        new_w_zoom = int(w_zoom * scale_zoom)
                        new_h_zoom = int(h_zoom * scale_zoom)
                        
                        img_resized_zoom = img_resized.resize((new_w_zoom, new_h_zoom), RESAMPLING_METHOD)
                        
                        # Pad to 2000x2000 square with white background if it's a studio/white-bg view
                        if has_white_bg and not is_zoom_view:
                            final_canvas = Image.new("RGB", (2000, 2000), (255, 255, 255))
                            paste_x = (2000 - new_w_zoom) // 2
                            paste_y = (2000 - new_h_zoom) // 2
                            final_canvas.paste(img_resized_zoom, (paste_x, paste_y))
                        else:
                            final_canvas = img_resized_zoom
                        
                        # Overwrite the zoom_dest
                        save_image_safe(final_canvas, zoom_dest, quality=92)
                        passed = True
                    else:
                        os.makedirs("scratch", exist_ok=True)
                        failure_info = {
                            "sku": sku,
                            "slot": slot,
                            "zoom_dest": os.path.abspath(zoom_dest),
                            "img_path": os.path.abspath(img_path)
                        }
                        failure_file = f"scratch/qa_failure_{sku}_{slot}.json"
                        with open(failure_file, 'w', encoding='utf-8') as f_fail:
                            json.dump(failure_info, f_fail, indent=2)
                
                final_canvas.close()
                img_resized.close()
                img_raw.close()

                
            results.append((slot, f"processed_studio_passed:{passed}"))
        except Exception as e:
            results.append((slot, f"error_studio: {e}"))
            
    return sku, results

def audit_zoom_outputs(curated_skus, zoom_dir, self_heal=True):
    print("\n--- STAGE 4: Auditing & Self-Healing Zoom Output Dimensions ---")
    audit_failures = 0
    healed = 0
    for prod_name, info, processed_slots in curated_skus:
        sku = info['sku'].strip()
        sorted_slots = sorted(processed_slots.keys())
        if not sorted_slots:
            continue
        main_slot_num = 1 if 1 in processed_slots else min(sorted_slots)

        for slot, img_info in processed_slots.items():
            is_studio = img_info.get('is_studio', False)
            is_zoom_view = img_info.get('is_zoom_view', False)
            has_white_bg = img_info.get('has_white_bg', True)

            is_main = (slot == main_slot_num)
            zoom_fn = f"{sku}_1.jpg" if is_main else f"{sku}_{slot}.jpg"
            zoom_path = os.path.join(zoom_dir, zoom_fn)

            # Only studio full-views are expected to be square.
            if not os.path.exists(zoom_path):
                continue
            if not (has_white_bg and not is_zoom_view):
                continue

            try:
                with Image.open(zoom_path) as img:
                    w, h = img.size
                    needs_heal = (w != h)
                    img_copy = img.convert('RGB').copy() if needs_heal else None
            except Exception as e:
                print(f"  [Audit Warning] Failed to inspect image {zoom_path}: {e}")
                continue

            if not needs_heal:
                continue

            audit_failures += 1
            print(f"  [Audit Failure] SKU {sku} Slot {slot} is non-square ({w}x{h}) but is a studio "
                  f"full-view (is_studio={is_studio}, has_white_bg={has_white_bg}, is_zoom_view={is_zoom_view}).")

            if self_heal:
                # Self-heal: a studio full-view must be square. Re-pad the existing render
                # onto a clean 2000x2000 white canvas, preserving aspect ratio and the
                # natural shadow (no re-segmentation, no GPU — safe to run sequentially).
                try:
                    longest = max(w, h)
                    scale = 2000.0 / longest
                    new_w = max(1, int(round(w * scale)))
                    new_h = max(1, int(round(h * scale)))
                    resized = img_copy.resize((new_w, new_h), RESAMPLING_METHOD)
                    square = Image.new("RGB", (2000, 2000), (255, 255, 255))
                    square.paste(resized, ((2000 - new_w) // 2, (2000 - new_h) // 2))
                    save_image_safe(square, zoom_path, quality=92)
                    resized.close()
                    square.close()
                    healed += 1
                    print(f"  [Audit Heal] SKU {sku} Slot {slot} re-padded to 2000x2000 square.")
                except Exception as e:
                    print(f"  [Audit Heal Warning] Failed to heal {zoom_path}: {e}")
                    os.makedirs("scratch", exist_ok=True)
                    failure_info = {
                        "sku": sku, "slot": slot,
                        "zoom_dest": os.path.abspath(zoom_path),
                        "error": f"Non-square studio full-view output: {w}x{h}"
                    }
                    with open(f"scratch/qa_failure_{sku}_audit.json", 'w', encoding='utf-8') as f_fail:
                        json.dump(failure_info, f_fail, indent=2)
            if img_copy is not None:
                img_copy.close()

    print(f"Audit complete. Found {audit_failures} non-square studio outputs, self-healed {healed}.")
    return audit_failures

def curate_sku(sku_clean):
    """
    Modular Stage 1: Ingestion & Curation for a single SKU.
    Determines slots, file locations, is_studio, is_zoom_view, and has_white_bg.
    Returns (prod_name, info, processed_slots) or None if not found.
    """
    sku_clean = sku_clean.strip()
    
    # Load brand sku dict
    if not os.path.exists(BRAND_DICT_PATH):
        print(f"  [Curation Error] Brand dictionary not found at {BRAND_DICT_PATH}")
        return None
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
        
    info = None
    prod_name = None
    for name, inf in brand_sku_dict.items():
        if inf['sku'].strip().lower() == sku_clean.lower():
            prod_name = name
            info = inf
            break
            
    if not info:
        print(f"  [Curation Error] SKU {sku_clean} not found in brand dictionary.")
        return None
        
    # Scanning logic
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
                    pr_name = m.group(1)
                    slot = int(m.group(2))
                    norm = normalize_name(pr_name)
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
                    s = sku_match.group(1).strip().lower()
                    orig_sku_folders[s] = p

    prod_norm = normalize_name(prod_name)
    raw_slots = {}
    
    # 0. Check local scratch downloads first (Stage 1 override from watcher)
    local_sku_dir = os.path.join(turboflow_dir, "scratch", "active_downloads", sku_clean)
    if os.path.isdir(local_sku_dir):
        for f in os.listdir(local_sku_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                slot = extract_slot_from_filename(f) or 1
                raw_slots[slot] = os.path.join(local_sku_dir, f)
        if raw_slots:
            print(f"  [Curation] Found {len(raw_slots)} raw slots in local active scratch folder.")
                
    if not raw_slots:
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
                    raw_slots[1] = p
            zoom_dir_path = os.path.join(dir_path, "zoom")
            if os.path.isdir(zoom_dir_path):
                for f in os.listdir(zoom_dir_path):
                    p = os.path.join(zoom_dir_path, f)
                    if os.path.isfile(p) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        slot = 2
                        slot_m = re.search(r'[-_](\d+)\.[a-zA-Z]+$', f)
                        if slot_m:
                            slot = int(slot_m.group(1))
                        raw_slots[slot] = p
                        
        # 2. Overlay TEST TOPAZ (2nd priority)
        if prod_norm in topaz_files:
            for slot, path in topaz_files[prod_norm]:
                raw_slots[slot] = path
                
        # 3. Overlay Refoma white background fix (1st priority)
        found_wb_fix_dir = None
        if os.environ.get("IGNORE_FIX_FOLDER") == "1":
            print(f"  [Curation] IGNORE_FIX_FOLDER env var is set. Skipping Refoma white background fix folder overlay.")
        else:
            name_norm = normalize_name(info['name'])
            slug_norm = normalize_name(prod_name)
            
            # 3.1 Try exact match after stripping leading digits from folder norm
            for f_norm, d_path in wb_fix_folders.items():
                f_norm_clean = re.sub(r'^\d+', '', f_norm)
                if name_norm == f_norm_clean or slug_norm == f_norm_clean:
                    found_wb_fix_dir = d_path
                    break
                    
            # 3.2 If still not found, collect substring matches on both name and slug and pick the closest
            if not found_wb_fix_dir:
                candidates = []
                for f_norm, d_path in wb_fix_folders.items():
                    f_norm_clean = re.sub(r'^\d+', '', f_norm)
                    if name_norm in f_norm_clean or f_norm_clean in name_norm:
                        candidates.append((len(f_norm_clean) - len(name_norm), d_path))
                    elif slug_norm in f_norm_clean or f_norm_clean in slug_norm:
                        candidates.append((len(f_norm_clean) - len(slug_norm), d_path))
                if candidates:
                    candidates.sort(key=lambda x: abs(x[0]))
                    found_wb_fix_dir = candidates[0][1]
                    
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
                    raw_slots[slot] = os.path.join(found_wb_fix_dir, best_cand)

    if not raw_slots:
        print(f"  [Curation Error] No raw slots found for SKU {sku_clean}.")
        return None
        
    cache = load_cache()
    bbox_db = load_bbox_db()
    gemini_key = load_gemini_key()
    
    processed_slots = {}
    category, _, _, _, _ = classify_and_size_product(prod_name)
    main_slot_num = 1 if 1 in raw_slots else min(raw_slots.keys())
    
    need_batch = False
    slots_to_query = {}
    sku_keys_info = {}
    
    for slot, img_path in raw_slots.items():
        img_key = f"{sku_clean}_{slot}_{get_file_sig(img_path)}"
        type_cache_key = f"type_{img_key}"
        bg_cache_key = f"has_white_bg_{img_key}"
        zoom_cache_key = f"zoom_{img_key}"
        
        has_semantics_cache = (type_cache_key in cache) and (bg_cache_key in cache)
        
        is_cand = False
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
                    is_cand = True
        except Exception:
            pass
            
        skip_margin_touch_heuristics = (slot == main_slot_num)
        if not is_cand and not skip_margin_touch_heuristics and bbox_db and img_key in bbox_db:
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
            if touches_top or touches_left or touches_right or is_large_closeup or touches_sides or touches_tb:
                is_cand = True
                
        need_zoom_status = is_cand and (zoom_cache_key not in cache)
        if not has_semantics_cache or need_zoom_status:
            need_batch = True
            
        slots_to_query[slot] = img_path
        sku_keys_info[slot] = {
            "img_key": img_key,
            "type_cache_key": type_cache_key,
            "bg_cache_key": bg_cache_key,
            "zoom_cache_key": zoom_cache_key
        }
        
    if need_batch and gemini_key:
        print(f"  [Classifier] Batch querying Gemini for SKU {sku_clean} ({len(slots_to_query)} images)...")
        batch_res = query_gemini_batch_for_sku(sku_clean, slots_to_query, gemini_key)
        if batch_res:
            for slot, res_data in batch_res.items():
                k_info = sku_keys_info[slot]
                cache[k_info["type_cache_key"]] = res_data["image_type"]
                cache[k_info["bg_cache_key"]] = res_data["has_white_bg"]
                cache[k_info["zoom_cache_key"]] = res_data["is_zoom_or_detail"]
            save_cache(cache)
            
    for slot, img_path in raw_slots.items():
        img_key = sku_keys_info[slot]["img_key"]
        type_cache_key = sku_keys_info[slot]["type_cache_key"]
        bg_cache_key = sku_keys_info[slot]["bg_cache_key"]
        
        if type_cache_key in cache and bg_cache_key in cache:
            img_type = cache[type_cache_key]
            has_white_bg = cache[bg_cache_key]
        else:
            semantics = classify_image_semantics_robust(img_path, gemini_key)
            img_type = semantics["image_type"]
            has_white_bg = semantics["has_white_bg"]
            cache[type_cache_key] = img_type
            cache[bg_cache_key] = has_white_bg
            
        is_studio = (img_type == "studio") or has_white_bg
        is_zoom_view = is_zoom_or_sketch(img_path, img_type, slot, img_key, cache, gemini_key, bbox_db=bbox_db, main_slot_num=main_slot_num)
        
        processed_slots[slot] = {
            "path": img_path,
            "img_key": img_key,
            "is_studio": is_studio,
            "is_zoom_view": is_zoom_view,
            "has_white_bg": has_white_bg
        }
        
    save_cache(cache)
    return (prod_name, info, processed_slots)

def segment_sku_gpu(sku_clean, curated_data, predictor=None):
    """
    Modular Stage 2: Grounded-SAM bbox generation.
    Uses Florence-2 to retrieve precise semantic coordinates, then runs SAM 3.
    """
    prod_name, info, processed_slots = curated_data
    category, _, _, _, _ = classify_and_size_product(prod_name)
    bbox_db = load_bbox_db()
    
    local_predictor_loaded = False
    if predictor is None:
        needs_sam3 = False
        for slot, img_info in processed_slots.items():
            if img_info['is_studio'] and not img_info['is_zoom_view']:
                img_key = img_info.get('img_key', f"{sku_clean}_{slot}")
                if img_key not in bbox_db:
                    needs_sam3 = True
                    break
        if needs_sam3:
            try:
                import torch
                from ultralytics.models.sam import SAM3SemanticPredictor
                print("Initializing SAM 3 semantic predictor on CUDA...")
                sam3_path = str(Path(__file__).resolve().parent.parent / "sam3.pt")
                overrides = dict(model=sam3_path, conf=0.10, device="cuda")
                predictor = SAM3SemanticPredictor(overrides=overrides)
                local_predictor_loaded = True
            except Exception as e:
                print(f"Could not load SAM3 on GPU: {e}. Falling back.")
                predictor = None
                
    if predictor is None:
        return
        
    import torch
    processed_sam3_count = 0
    
    for slot, img_info in processed_slots.items():
        if img_info['is_studio'] and not img_info['is_zoom_view']:
            img_key = img_info.get('img_key', f"{sku_clean}_{slot}")
            if img_key in bbox_db:
                continue
                
            img_path = img_info['path']
            print(f"  Running Grounded-SAM on CUDA for {img_key}...")
            
            try:
                with Image.open(img_path) as img_raw:
                    w_orig, h_orig = img_raw.size
                    longest = max(w_orig, h_orig)
                    scale_init = 2000.0 / longest
                    new_w = int(w_orig * scale_init)
                    new_h = int(h_orig * scale_init)
                    img_resized = img_raw.resize((new_w, new_h), RESAMPLING_METHOD)
                    
                # Run Florence-2 phrase grounding
                florence_bbox = None
                text_prompts = get_sam3_text_prompt(category, prod_name)
                primary_prompt = text_prompts[0]
                
                # Retrieve bounding box from VLM
                detected_box = query_florence2_bbox(img_path, primary_prompt)
                
                if detected_box:
                    x_min_orig, y_min_orig, x_max_orig, y_max_orig = detected_box
                    # Scale coordinates to match resized image (2000px longest side)
                    florence_bbox = [
                        int(x_min_orig * scale_init),
                        int(y_min_orig * scale_init),
                        int(x_max_orig * scale_init),
                        int(y_max_orig * scale_init)
                    ]
                    # Clamp bounding box coordinates
                    florence_bbox = [
                        max(0, min(new_w, florence_bbox[0])),
                        max(0, min(new_h, florence_bbox[1])),
                        max(0, min(new_w, florence_bbox[2])),
                        max(0, min(new_h, florence_bbox[3]))
                    ]
                    print(f"    [Grounded-SAM] Local Florence-2 detected '{primary_prompt}' coordinates: {florence_bbox}")
                
                with torch.no_grad():
                    if florence_bbox:
                        # Feed Florence-2 bounding box into SAM3
                        results = predictor(img_resized, bboxes=[florence_bbox], text=text_prompts)
                    else:
                        results = predictor(img_resized, text=text_prompts)
                    
                if len(results) > 0 and results[0].masks is not None:
                    masks_tensor = results[0].masks.data
                    combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy()
                    # Exclude 15px borders
                    combined_mask[:15, :] = False
                    combined_mask[-15:, :] = False
                    combined_mask[:, :15] = False
                    combined_mask[:, -15:] = False
                    
                    coords_body = np.argwhere(combined_mask > 0)
                    if coords_body.size > 0:
                        y_min_clean = int(coords_body[:, 0].min())
                        y_max_clean = int(coords_body[:, 0].max())
                        x_min_clean = int(coords_body[:, 1].min())
                        x_max_clean = int(coords_body[:, 1].max())
                        
                        bbox_db[img_key] = [x_min_clean, y_min_clean, x_max_clean, y_max_clean]
                        processed_sam3_count += 1
                        save_bbox_db(bbox_db)
                        
                img_resized.close()
            except Exception as e:
                print(f"    Warning: Grounded-SAM failed for {img_key}: {e}")
                
    save_bbox_db(bbox_db)
    
    if local_predictor_loaded:
        predictor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("VRAM cleared after local predictor usage.")

def compose_sku_cpu(sku_clean, curated_data):
    """
    Modular Stage 3: CPU Image Composition & QA check.
    Saves outputs in artiklar, liten, and zoom folders.
    """
    prod_name, info, processed_slots = curated_data
    
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    bbox_db = load_bbox_db()
    task = (prod_name, info, processed_slots, bbox_db, artiklar_dir, liten_dir, zoom_dir)
    
    sku_res, results = process_sku_cpu_worker(task)
    audit_zoom_outputs([curated_data], zoom_dir)
    return results

def run_pipeline(limit_sku=None, limit_val=None, dry_run=False):
    print("==================================================")
    print("      DECOUPLED STAGED IMAGE PROCESSING PIPELINE  ")
    print("==================================================")
    
    gemini_key = load_gemini_key()
    if not gemini_key:
        print("[WARNING] GEMINI_API_KEY.env not found. Gemini queries will be skipped and fallback to defaults.")
        
    if not os.path.exists(BRAND_DICT_PATH):
        print(f"[ERROR] Brand dictionary not found: {BRAND_DICT_PATH}")
        return
        
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
        
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    if not dry_run:
        print(f"Ensuring output directories exist: {FTP_UPLOAD_DIR}")
        for d in (artiklar_dir, liten_dir, zoom_dir):
            os.makedirs(d, exist_ok=True)
            for f in os.listdir(d):
                p_file = os.path.join(d, f)
                if os.path.isfile(p_file):
                    is_match = False
                    if limit_sku is None:
                        is_match = True
                    elif isinstance(limit_sku, list):
                        is_match = any(f.lower().startswith(s.lower()) for s in limit_sku)
                    else:
                        is_match = f.lower().startswith(limit_sku.lower())
                    
                    if is_match:
                        try:
                            os.remove(p_file)
                        except Exception:
                            pass
    else:
        print("\n*** RUNNING IN DRY-RUN MODE (No output files written) ***")

    # Filter products to process
    products_to_process = list(brand_sku_dict.items())
    if limit_sku:
        if isinstance(limit_sku, list):
            limit_skus_lower = [s.strip().lower() for s in limit_sku]
            products_to_process = [(name, info) for name, info in products_to_process if info['sku'].strip().lower() in limit_skus_lower]
            print(f"Limiting to list of {len(limit_sku)} SKUs. Found matches: {len(products_to_process)}")
        else:
            products_to_process = [(name, info) for name, info in products_to_process if info['sku'].strip().lower() == limit_sku.lower()]
            print(f"Limiting to SKU: {limit_sku}. Found matches: {len(products_to_process)}")
    elif limit_val is not None:
        products_to_process = products_to_process[:limit_val]
        print(f"Limiting to first {limit_val} items.")
    elif dry_run:
        products_to_process = products_to_process[:10]
        
    print(f"\nProcessing {len(products_to_process)} total products...")

    # ----------------------------------------------------
    # STAGE 1: Curation & Ingestion (CPU)
    # ----------------------------------------------------
    print("\n--- STAGE 1: Ingestion & Curation ---")
    curated_skus = []
    for name, info in products_to_process:
        sku = info['sku'].strip()
        print(f"Curating SKU: {sku}...")
        curated = curate_sku(sku)
        if curated:
            curated_skus.append(curated)
    print(f"Ingested and curated metadata for {len(curated_skus)} SKUs.")

    if not curated_skus:
        print("No SKUs to process. Exiting.")
        return

    # ----------------------------------------------------
    # STAGE 2: Sequential GPU BBox Generation (SAM3)
    # ----------------------------------------------------
    print("\n--- STAGE 2: Sequential GPU SAM3 BBox Generation ---")
    bbox_db = load_bbox_db()
    needs_sam3 = False
    for prod_name, info, processed_slots in curated_skus:
        for slot, img_info in processed_slots.items():
            if img_info['is_studio'] and not img_info['is_zoom_view']:
                img_key = img_info.get('img_key', f"{info['sku']}_{slot}")
                if img_key not in bbox_db:
                    needs_sam3 = True
                    break
        if needs_sam3:
            break
            
    if needs_sam3:
        try:
            import torch
            from ultralytics.models.sam import SAM3SemanticPredictor
            print("Initializing SAM 3 semantic predictor on CUDA...")
            sam3_path = str(Path(__file__).resolve().parent.parent / "sam3.pt")
            overrides = dict(model=sam3_path, conf=0.10, device="cuda")
            predictor = SAM3SemanticPredictor(overrides=overrides)
            print("SAM3 loaded successfully on GPU.")
        except Exception as e:
            print(f"Could not load SAM3 on GPU: {e}. Falling back to default thresholds.")
            predictor = None
    else:
        print("All required bounding boxes already exist in scratch/bbox_coordinates_db.json. Skipping GPU initialization.")
        predictor = None

    if predictor is not None:
        for prod_name, info, processed_slots in curated_skus:
            sku = info['sku'].strip()
            segment_sku_gpu(sku, (prod_name, info, processed_slots), predictor=predictor)
        
        # Explicitly unload model and release CUDA cache
        predictor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("VRAM cleared after Stage 2.")

    # ----------------------------------------------------
    # STAGE 3: Parallel CPU Composition Pool (CPU)
    # ----------------------------------------------------
    print("\n--- STAGE 3: Parallel CPU Image Composition ---")
    if dry_run:
        print("Dry run mode: Skipping Stage 3 rendering.")
        return
        
    sku_tasks = []
    for prod_name, info, processed_slots in curated_skus:
        sku_tasks.append((prod_name, info, processed_slots, load_bbox_db(), artiklar_dir, liten_dir, zoom_dir))
        
    print(f"Spawning parallel CPU composition workers for {len(sku_tasks)} SKUs...")
    num_workers = min(os.cpu_count() or 4, 8)
    print(f"Using {num_workers} parallel CPU workers.")
    
    completed_count = 0
    if len(sku_tasks) == 1:
        task = sku_tasks[0]
        sku = task[1]['sku']
        try:
            sku_clean, results = process_sku_cpu_worker(task)
            completed_count += 1
            print(f"[{completed_count}/1] SKU {sku_clean} finished. Results: {dict(results)}")
        except Exception as e:
            print(f"❌ Error processing SKU {sku} in main thread: {e}")
    else:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(process_sku_cpu_worker, task): task[1]['sku'] for task in sku_tasks}
            
            for future in as_completed(futures):
                sku = futures[future]
                try:
                    sku_clean, results = future.result()
                    completed_count += 1
                    print(f"[{completed_count}/{len(sku_tasks)}] SKU {sku_clean} finished. Results: {dict(results)}")
                except Exception as e:
                    print(f"❌ Error processing SKU {sku} in CPU worker: {e}")
                
    # Run audit zoom outputs
    audit_zoom_outputs(curated_skus, zoom_dir)
                
    print("\n==================================================")
    print("      DECOUPLED STAGED PIPELINE COMPLETED         ")
    print("==================================================")

if __name__ == "__main__":
    import sys
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
    run_pipeline(limit_sku=limit_sku, limit_val=limit_val)

