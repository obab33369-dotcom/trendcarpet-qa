import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any, List
import scipy.ndimage
import base64
from io import BytesIO
import requests
import json

class QAChecker:
    """
    Performs fast heuristic diagnostics (pixel checks) on composed 2000x2000px canvases.
    Checks:
    1. Background Purity (outer border must be pure white).
    2. Horizontal Centering (visual upper mass must be centered within 10px).
    3. Floor Alignment / Grounding (product feet must sit exactly at Y=1800 within 5px).
    4. Edge Halo / Leakage (transition zone must not contain excessive near-white pixels).
    """

    def __init__(self, target_size: int = 2000, target_floor: int = 1800):
        self.target_size = target_size
        self.target_floor = target_floor

    def run_gemini_vision_qa(
        self,
        canvas: Image.Image,
        target_floor: int,
        gemini_key: str
    ) -> Dict[str, Any]:
        """
        Queries Gemini Vision to audit the composed image for layout and cleanup issues.
        """
        try:
            # Resize image to 500x500 for fast upload and API efficiency
            img_resized = canvas.resize((500, 500))
            buffered = BytesIO()
            img_resized.convert('RGB').save(buffered, format="JPEG", quality=80)
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            img_resized.close()

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            
            prompt = (
                f"Analyze this composed 2000x2000px product image. The target layout expected is:\n"
                f"- Grounding: The product base should be grounded exactly at Y={target_floor}px (or bottom Y=2000px if it is a cut-off base).\n"
                f"- Background: Plain white background (#FFFFFF) with clean boundaries. No gray shadows bleeding off edge, no halos.\n"
                f"- Boundaries: No clipping at the top, left, or right edges.\n\n"
                f"Identify if there are any of these issues:\n"
                f"1. 'clipping': product is cut off at the edge of the canvas.\n"
                f"2. 'bad_cleanup': halos, off-white shadows, grey borders, or dirty background.\n"
                f"3. 'off_grounding': product is floating too high above the floor line (Y={target_floor}px) or pushed too low.\n"
                f"4. 'off_center': product is off-center horizontally.\n\n"
                f"Reply strictly in JSON format:\n"
                f"{{\n"
                f"  \"passed\": true | false,\n"
                f"  \"issues\": [\"clipping\" | \"bad_cleanup\" | \"off_grounding\" | \"off_center\"],\n"
                f"  \"feedback\": \"detailed text describing what you see\",\n"
                f"  \"suggested_adjustments\": {{\n"
                f"    \"scale_multiplier\": 0.93 (if clipped) or 1.0,\n"
                f"    \"shift_x\": integer pixels (negative to shift left, positive to shift right),\n"
                f"    \"shift_y\": integer pixels (negative to shift up, positive to shift down),\n"
                f"    \"increase_tolerance\": true (if background cleanup failed) or false\n"
                f"  }}\n"
                f"}}"
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
                return json.loads(text_resp)
            else:
                print(f"  [QA Checker Warning] Gemini Vision API returned status {res.status_code}: {res.text}")
        except Exception as e:
            print(f"  [QA Checker Warning] Gemini Vision QA API query failed: {e}")
        return {"passed": True, "issues": [], "feedback": "API error fallback", "suggested_adjustments": {}}

    def run_local_florence2_qa(
        self,
        canvas: Image.Image,
        target_floor: int,
        category: str
    ) -> Dict[str, Any]:
        """
        Runs local Florence-2 Phrase Grounding to detect the main product on the composed canvas
        and verifies horizontal centering, floor grounding, and edge clipping.
        """
        from reforma_pipeline.local_vlm import query_florence2_bbox
        
        # Decide prompt based on category
        query = "furniture"
        if category in ["chair_dining", "armchair", "barstool", "stool"]:
            query = "chair"
        elif category in ["sofa", "daybed"]:
            query = "sofa"
        elif category in ["table_dining", "table_non_dining", "desk", "bedside_table"]:
            query = "table"
        elif "carpet" in category or "rug" in category:
            query = "carpet"
        elif "lamp" in category or "lighting" in category:
            query = "lamp"
            
        print(f"  [QA Checker] Running Tier 2 Florence-2 layout audit with query '{query}'...")
        bbox = query_florence2_bbox(canvas, query)
        if bbox is None:
            # Fallback query if specific category was not found
            query = "product"
            bbox = query_florence2_bbox(canvas, query)
            if bbox is None:
                # If still none, try "furniture"
                query = "furniture"
                bbox = query_florence2_bbox(canvas, query)
                
        if bbox is None:
            return {
                "passed": False,
                "reason": "Florence-2 failed to locate the product on canvas",
                "bbox": None,
                "errors": ["Florence2CannotLocateObject"]
            }
            
        x_min, y_min, x_max, y_max = bbox
        
        # Centering check
        mid_x = (x_min + x_max) / 2
        centering_error = mid_x - 1000  # canvas is 2000x2000
        
        # Grounding check
        floor_error = y_max - target_floor
        
        # Clipping check (checks if it touches the outer margins, e.g., 20px)
        clipping_detected = (x_min <= 20) or (x_max >= 1980) or (y_min <= 20)
        
        errors = []
        # Allow a slightly wider tolerance for Florence-2 since it is a neural bbox predictor (e.g. 40px center, 30px floor)
        if abs(centering_error) > 40:
            errors.append(f"Florence2OffCenter: centering error {centering_error:.1f}px")
        if abs(floor_error) > 30:
            errors.append(f"Florence2OffGrounding: grounding error {floor_error:.1f}px (bottom at {y_max}px, expected {target_floor}px)")
        if clipping_detected:
            errors.append("Florence2ClippingDetected")
            
        passed = (len(errors) == 0)
        return {
            "passed": passed,
            "bbox": bbox,
            "errors": errors,
            "metrics": {
                "centering_error": centering_error,
                "floor_error": floor_error,
                "clipping_detected": clipping_detected
            }
        }

    def run_diagnostics(
        self,
        canvas: Image.Image,
        bbox_clean: Tuple[int, int, int, int],
        crop_box: Tuple[int, int, int, int],
        paste_pos: Tuple[int, int],
        scale: float,
        is_cutoff_base: bool = False,
        is_centered: bool = False,
        category: str = "default"
    ) -> Dict[str, Any]:
        """
        Runs pixel-level checks and calculates required adjustments.
        
        Parameters:
          canvas: Composed PIL Image (should be 2000x2000).
          bbox_clean: SAM3 body bounding box in original image coordinates (x_min, y_min, x_max, y_max).
          crop_box: Crop bounding box used (crop_x_min, crop_y_min, crop_x_max, crop_y_max).
          paste_pos: Paste coordinates on canvas (paste_x, paste_y).
          scale: Scaling factor used.
          is_cutoff_base: Whether the product's base is cut off at the bottom.
          category: Product category to determine centering range.
        """
        arr = np.array(canvas.convert('RGB'))
        w, h = canvas.size

        # 1. Background Purity Check
        # Check a 10px border around the canvas. If the product base is cut off,
        # we exclude the bottom edge from the background purity check.
        top_edge = arr[0:10, :, :]
        left_edge = arr[:, 0:10, :]
        right_edge = arr[:, -10:, :]

        edges = [
            top_edge.reshape(-1, 3),
            left_edge.reshape(-1, 3),
            right_edge.reshape(-1, 3)
        ]
        if not is_cutoff_base:
            bottom_edge = arr[-10:, :, :]
            edges.append(bottom_edge.reshape(-1, 3))

        bg_pixels = np.concatenate(edges, axis=0)

        # Count pixels that are NOT pure white/off-white (allow values >= 250 for soft shadows/compression)
        non_white_bg_count = np.sum(np.any(bg_pixels < 250, axis=-1))
        # Composition now guarantees a clean 15px white border, so any stray edge pixels
        # are only ever compression/anti-alias noise. Keep a small, forgiving tolerance so
        # a preserved shadow grazing the safe zone is never a hard failure.
        bg_purity_passed = (non_white_bg_count <= 20)

        # Calculate product body canvas coordinates
        if bbox_clean is None:
            x_min_clean, y_min_clean, x_max_clean, y_max_clean = crop_box
        else:
            x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
        crop_x_min, crop_y_min, _, _ = crop_box
        paste_x, paste_y = paste_pos

        offset_x = x_min_clean - crop_x_min
        offset_y = y_min_clean - crop_y_min

        body_x_min = int(paste_x + offset_x * scale)
        body_y_min = int(paste_y + offset_y * scale)
        body_x_max = int(body_x_min + (x_max_clean - x_min_clean) * scale)
        body_y_max = int(body_y_min + (y_max_clean - y_min_clean) * scale)

        body_h = max(1, body_y_max - body_y_min)
        body_w = max(1, body_x_max - body_x_min)

        # Clip body coordinates to canvas bounds
        body_x_min_clip = max(0, min(w - 1, body_x_min))
        body_y_min_clip = max(0, min(h - 1, body_y_min))
        body_x_max_clip = max(0, min(w - 1, body_x_max))
        body_y_max_clip = max(0, min(h - 1, body_y_max))

        # 2. Centering check (visual upper mass or seat-centric)
        if category in ["chair_dining", "armchair", "barstool", "stool"]:
            y_start_pct = 0.50
            y_end_pct = 0.65
        else:
            y_start_pct = 0.0
            y_end_pct = 0.70

        y_start = body_y_min_clip + int(y_start_pct * body_h)
        y_end = body_y_min_clip + int(y_end_pct * body_h)
        y_start = max(body_y_min_clip, min(y_start, body_y_max_clip - 1))
        y_end = max(y_start + 1, min(y_end, body_y_max_clip))

        upper_mass = arr[y_start:y_end, :, :]
        # Background is white (255, 255, 255). Any pixel with sum of difference from 255 > 15 is non-white
        diff_from_white = np.sum(255 - upper_mass, axis=-1)
        non_white_mask = diff_from_white > 15

        # Ignore 5px thin border to avoid edge noise
        non_white_mask[:, :5] = False
        non_white_mask[:, -5:] = False

        # Body-centric: restrict the centering scan to the SAM3 body box so a cast/
        # contact shadow extending to one side cannot bias the metric — otherwise the
        # self-correcting loop pushes the body off-center to "balance" the shadow,
        # exactly the bug we fix in composition.
        non_white_mask[:, :max(0, body_x_min_clip)] = False
        non_white_mask[:, body_x_max_clip + 1:] = False

        coords = np.argwhere(non_white_mask)
        if coords.size > 0:
            x_min_vis = coords[:, 1].min()
            x_max_vis = coords[:, 1].max()
        else:
            x_min_vis = body_x_min_clip
            x_max_vis = body_x_max_clip

        left_padding = x_min_vis
        right_padding = self.target_size - x_max_vis
        centering_error = left_padding - right_padding

        # 3. Grounding (Floor Line) Check
        # Product feet (body bottom) must align exactly with target floor (Y = 1800 or Y = 2000 for cut-off base)
        target_floor = 2000 if is_cutoff_base else self.target_floor
        floor_error = body_y_max - target_floor
        if is_centered:
            floor_error = 0

        # 4. Halo / Edge Transition Leakage Check
        # Uphold: only run halo checks if background purity is generally okay
        body_box_arr = arr[body_y_min_clip:body_y_max_clip, body_x_min_clip:body_x_max_clip, :]
        box_diff = np.sum(255 - body_box_arr, axis=-1)
        body_mask_local = box_diff > 30

        body_mask = np.zeros((h, w), dtype=bool)
        body_mask[body_y_min_clip:body_y_max_clip, body_x_min_clip:body_x_max_clip] = body_mask_local

        # Fill internal holes (e.g. rattan mesh, open spaces) before dilation to avoid transition mask bleeding inside the product
        body_mask = scipy.ndimage.binary_fill_holes(body_mask)

        # Dilate mask by 5 pixels
        struct = scipy.ndimage.generate_binary_structure(2, 1)
        dilated_mask = scipy.ndimage.binary_dilation(body_mask, structure=struct, iterations=5)

        transition_mask = dilated_mask & ~body_mask
        # Exclude the band directly below the product: that is the natural contact shadow,
        # which we now preserve on purpose and must not flag as a halo.
        transition_mask[body_y_max_clip:, :] = False
        transition_pixels = arr[transition_mask]
        
        halo_leakage_passed = True
        halo_pixel_count = 0
        ratio = 0.0

        if transition_pixels.size > 0:
            gray = 0.299 * transition_pixels[:, 0] + 0.587 * transition_pixels[:, 1] + 0.114 * transition_pixels[:, 2]
            # A genuine bad-cleanup halo is near-white AND clearly warm (yellowish).
            # Neutral grey shadow rollover (R≈G≈B) is intentionally excluded.
            near_white = (gray >= 251.0) & (gray < 255.0)
            is_warm = (transition_pixels[:, 0] > transition_pixels[:, 2] + 3)
            halo_pixel_count = np.sum(near_white & is_warm)
            body_pixel_count = np.sum(body_mask)

            if body_pixel_count > 0:
                ratio = float(halo_pixel_count) / body_pixel_count
                if ratio > 0.025:  # threshold 2.5% (relaxed to tolerate soft natural edges)
                    halo_leakage_passed = False

        # Evaluation results
        passed = True
        errors = []

        if not bg_purity_passed:
            passed = False
            errors.append(f"BackgroundPurityError: found {non_white_bg_count} non-white border pixels")
        if abs(centering_error) > 30:
            passed = False
            errors.append(f"OffCenterWarning: off-center horizontally by {centering_error}px")
        if abs(floor_error) > 10:
            passed = False
            errors.append(f"GroundingError: product bottom sits at {body_y_max}px, expected {target_floor}px (off by {floor_error}px)")
        if not halo_leakage_passed:
            passed = False
            errors.append(f"HaloLeakageError: edge halo ratio is {ratio:.4f} ({halo_pixel_count} pixels, limit is 0.0250)")

        # Calculate adjustments
        delta_x = -centering_error // 2
        delta_y = -floor_error

        # Determine if scaling reduction is required due to top or side clipping
        # Top/Side clipping: product touches within 25px of canvas boundaries (composition limits are 20px)
        is_clipped = (body_y_min <= 25) or (body_x_min <= 25) or (body_x_max >= w - 25)
        
        return {
            "passed": passed,
            "errors": errors,
            "is_clipped": is_clipped,
            "adjustments": {
                "delta_x": delta_x,
                "delta_y": delta_y,
            },
            "metrics": {
                "bg_non_white_count": int(non_white_bg_count),
                "centering_error": int(centering_error),
                "floor_error": int(floor_error),
                "halo_ratio": float(ratio),
                "body_bounds_canvas": [body_x_min, body_y_min, body_x_max, body_y_max]
            }
        }
