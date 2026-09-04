import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional

class CompositionEngine:
    """
    Crops, scales, and aligns images based on body bounding box and shadow offsets.
    Implements body-centric centering to solve asymmetric shadow alignment bugs.
    """
    
    def __init__(self, target_size: int = 2000):
        self.target_size = target_size
        # Cache for sharing scale factors among Hero views (Slot 1-6) of the same SKU
        self.scale_cache: Dict[str, float] = {}
        # Cache for storing the product height of the main slot of each SKU
        self.height_cache: Dict[str, float] = {}

    def get_shadow_bbox(self, img: Image.Image, bg_color: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Detects bounding box of all non-white pixels (product body + natural shadow).
        """
        arr = np.array(img.convert('RGB'))
        diff = np.sum(np.abs(arr - bg_color), axis=-1)
        
        # Buffer tolerance (15 diff is non-white)
        non_white = diff > 15
        # Exclude thin 5px borders to ignore edge noise
        non_white[:5, :] = False
        non_white[-5:, :] = False
        non_white[:, :5] = False
        non_white[:, -5:] = False
        
        coords = np.argwhere(non_white)
        if coords.size == 0:
            raise ValueError("No shadow or product pixels detected.")
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        return (int(x_min), int(y_min), int(x_max), int(y_max))

    def get_visual_body_bounds(self, img_cleaned: Image.Image, bbox_clean: Tuple[int, int, int, int], category: str = "default") -> Tuple[int, int]:
        """
        Horizontal extent (x_min, x_max) of the FURNITURE BODY used for centering,
        derived strictly from the SAM3 body bbox (which excludes the cast/contact
        shadow). A shadow extending to one side can therefore never pull centering
        off-axis. For seat-based items we refine to the seat band, but the search is
        always clipped to [x_min_clean, x_max_clean] so only body pixels are seen.
        """
        w_img = img_cleaned.size[0]
        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
        x_min_clean = int(max(0, min(w_img, x_min_clean)))
        x_max_clean = int(max(0, min(w_img, x_max_clean)))
        if x_max_clean <= x_min_clean:
            return x_min_clean, x_max_clean

        # Non-seat items: the SAM3 body box IS the visual body (shadow-free).
        if category not in ("chair_dining", "armchair", "barstool", "stool"):
            return x_min_clean, x_max_clean

        # Seat-based items: center on the seat band (immune to splayed legs), but only
        # look at pixels INSIDE the body box so floor shadow is never counted.
        h_p = max(1, y_max_clean - y_min_clean)
        y_start = max(y_min_clean, min(y_min_clean + int(0.50 * h_p), y_max_clean - 1))
        y_end = max(y_start + 1, min(y_min_clean + int(0.65 * h_p), y_max_clean))

        arr = np.array(img_cleaned.convert('RGB'))
        band = arr[y_start:y_end, x_min_clean:x_max_clean, :]
        non_white = np.sum(255 - band, axis=-1) > 15
        coords = np.argwhere(non_white)
        if coords.size > 0:
            return x_min_clean + int(coords[:, 1].min()), x_min_clean + int(coords[:, 1].max())
        return x_min_clean, x_max_clean


    def compose_studio_image(
        self,
        img: Image.Image,
        bbox_clean: Optional[Tuple[int, int, int, int]],  # Body-only bbox (from SAM3)
        category: str,
        sku: str,
        slot: int,
        is_zoom_view: bool,
        bg_color: np.ndarray,
        target_w: float,
        target_h: float,
        floor_pct: float,
        is_centered: bool,
        sku_scale: Optional[float] = None,
        has_white_bg: bool = True,
        adjust_x: int = 0,
        adjust_y: int = 0
    ) -> Tuple[Image.Image, float, Tuple[int, int, int, int], Tuple[int, int]]:
        """
        Crops including the shadow, but calculates scale and centering translations
        purely based on the product body coordinates (solving centering bugs).
        Supports adjust_x and adjust_y overrides for self-correcting loop.
        
        Returns a tuple of (composed_image, scale_used, crop_box, paste_pos).
        """
        w, h = img.size
        
        # 1. Detect if product has a cut-off base (touches bottom of the original image)
        is_cutoff_base = False
        if bbox_clean is not None:
            _, _, _, y_max_clean = bbox_clean
            if y_max_clean >= h - 10:
                is_cutoff_base = True

        # 2. Sizing-only route for zoom/detail/close-ups/lifestyle/sketches
        if is_zoom_view:
            # Sizing Rule: Simply resize so that the longest side is 2000px, preserving original aspect ratio.
            # Do NOT crop, do NOT pad with white margins/borders, and do NOT alter aspect ratio or feather.
            longest = max(w, h)
            scale = 2000.0 / longest
            new_w = int(w * scale)
            new_h = int(h * scale)
            resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            return resized_img, scale, (0, 0, w, h), (0, 0)

        # 3. Studio cutout views (slots 1-6) composed on 2000x2000px canvas
        # Shadow BBox Extraction
        arr_img = np.array(img.convert('RGB'))
        patches = [arr_img[10:25, 10:25], arr_img[10:25, -25:-10], arr_img[-25:-10, 10:25], arr_img[-25:-10, -25:-10]]
        means = [np.mean(pat, axis=(0,1)) for pat in patches]
        means.sort(key=lambda c: np.sum(c))
        detected_bg = np.mean(means[1:], axis=0)

        try:
            x_min_raw, y_min_raw, x_max_raw, y_max_raw = self.get_shadow_bbox(img, detected_bg)
        except ValueError:
            if bbox_clean is not None:
                x_min_raw, y_min_raw, x_max_raw, y_max_raw = bbox_clean
            else:
                x_min_raw, y_min_raw, x_max_raw, y_max_raw = 0, 0, w, h

        # Fallback if SAM3 didn't run or failed
        if bbox_clean is None:
            bbox_clean = (x_min_raw, y_min_raw, x_max_raw, y_max_raw)

        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
        
        # If fallback shadow detection touches bottom, set cutoff base flag
        if bbox_clean is None and y_max_raw >= h - 10:
            is_cutoff_base = True
        
        # Body Dimensions
        W_p = max(1.0, float(x_max_clean - x_min_clean))
        H_p = max(1.0, float(y_max_clean - y_min_clean))
        
        # Crop box includes the shadow plus an ADAPTIVE white margin. The margin is sized
        # relative to the image so the crop boundary lands in genuinely white space (where
        # the shadow's natural alpha has already decayed to ~0). Extra room is reserved
        # below the product to hold the contact/cast shadow's natural rollover. This is
        # what lets us "crop the image as it is" without the shadow meeting a hard line.
        longest_side = float(max(w, h))
        pad_x = max(40, int(0.035 * longest_side))
        pad_top = max(20, int(0.035 * longest_side))
        pad_bottom = max(40, int(0.07 * longest_side))
        crop_x_min = max(5 if x_min_raw >= 5 else max(0, x_min_raw), x_min_raw - pad_x)
        crop_y_min = max(5 if y_min_raw >= 5 else max(0, y_min_raw), y_min_raw - pad_top)
        crop_x_max = min(w - 5 if x_max_raw <= w - 5 else min(w, x_max_raw), x_max_raw + pad_x)
        crop_y_max = min(h - 5 if y_max_raw <= h - 5 else min(h, y_max_raw), y_max_raw + pad_bottom)
        
        cropped_area = img.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
        w_c, h_c = cropped_area.size
        
        # Load cropped area as numpy array for pixel-level layering
        arr_crop = np.array(cropped_area.convert('RGB')).astype(np.float32)
        
        # Calculate luma for shadow transparency formula
        luma = 0.299 * arr_crop[:, :, 0] + 0.587 * arr_crop[:, :, 1] + 0.114 * arr_crop[:, :, 2]
        
        # Identify product body region inside the cropped area
        body_x1 = max(0, x_min_clean - crop_x_min)
        body_y1 = max(0, y_min_clean - crop_y_min)
        body_x2 = min(w_c, x_max_clean - crop_x_min)
        body_y2 = min(h_c, y_max_clean - crop_y_min)
        
        # Generate pixel-level product body mask (any non-white pixel inside body bbox)
        product_mask = np.zeros((h_c, w_c), dtype=bool)
        if body_x2 > body_x1 and body_y2 > body_y1:
            body_arr = arr_crop[body_y1:body_y2, body_x1:body_x2]
            body_non_white = np.sum(255.0 - body_arr, axis=-1) > 15
            product_mask[body_y1:body_y2, body_x1:body_x2] = body_non_white
            
        # Shadow rollover / falloff: roll the shadow's alpha smoothly to zero over the
        # outermost band of the crop. With the generous padding above, this band sits in
        # white space for shadows that fit inside the frame (so it is INVISIBLE), and it
        # gently softens the edge for shadows cut off by the source photo (so a straight
        # hard line never appears). Smoothstep gives a natural, non-linear rollover.
        roll = max(24, int(0.45 * pad_x))
        roll = min(roll, max(1, (min(w_c, h_c) // 2) - 1))

        def _smoothstep_ramp(length, width):
            r = np.ones(length, dtype=np.float32)
            if width > 0 and length > 2 * width:
                i = np.arange(length, dtype=np.float32)
                r = np.minimum(np.clip(i / width, 0.0, 1.0),
                               np.clip((length - 1 - i) / width, 0.0, 1.0))
                r = r * r * (3.0 - 2.0 * r)
            return r

        ramp_x = _smoothstep_ramp(w_c, roll)
        if is_cutoff_base:
            # Preserve the contact shadow all the way to the bottom for cut-off bases:
            # roll off only the TOP of the shadow, keep the bottom intact.
            i_y = np.arange(h_c, dtype=np.float32)
            ramp_y = np.clip(i_y / max(1, roll), 0.0, 1.0)
            ramp_y = ramp_y * ramp_y * (3.0 - 2.0 * ramp_y)
        else:
            ramp_y = _smoothstep_ramp(h_c, roll)
        shadow_rolloff = np.outer(ramp_y, ramp_x)

        # --- Shadow policy: PRESERVE the original retouched/contact shadow ----------
        # We never rebuild a synthetic ACSS shadow for the hero path; that recreation
        # (luma mask + feather ramp) is what destroyed the soft natural shadows.
        # Keep the whole cropped area as ONE solid layer. On for any genuine white
        # background (the only kind routed here) and forceable with FORCE_ORIGINAL=1.
        import os
        bg_is_pure_white = (float(np.mean(detected_bg)) >= 250.0
                            and float(np.max(detected_bg) - np.min(detected_bg)) <= 6.0)
        preserve_original = (os.environ.get("FORCE_ORIGINAL") == "1") or bool(has_white_bg) or bg_is_pure_white

        if preserve_original:
            # Keep the entire cropped area intact (including product + original shadow), fully solid.
            # We will clean up and fade the edges after scaling/resizing to prevent compression and interpolation artifacts.
            product_img = cropped_area.convert("RGBA")
            # Create an empty shadow layer so nothing is pasted there
            shadow_rgba = np.zeros((h_c, w_c, 4), dtype=np.uint8)
            shadow_img = Image.fromarray(shadow_rgba, mode="RGBA")
        else:
            # Construct Shadow Alpha Layer (ACSS)
            # Alpha = 1.0 - (Luma / 255.0). Pure black color is used to represent the shadow.
            shadow_alpha = 1.0 - (luma / 255.0)
            # Apply 0.95 threshold clipping (if pixel is nearly white, force Alpha = 0.0)
            shadow_alpha[luma / 255.0 > 0.95] = 0.0
            # Exclude the product body so the shadow never double-darkens the product edge.
            shadow_alpha[product_mask] = 0.0
            # Apply the smooth shadow rollover (interior shadow is preserved fully).
            shadow_alpha = np.clip(shadow_alpha * shadow_rolloff, 0.0, 1.0)
            
            # Build transparent Shadow Layer (RGBA)
            shadow_rgba = np.zeros((h_c, w_c, 4), dtype=np.uint8)
            # RGB = (0,0,0) (neutral black); A = calculated alpha
            shadow_rgba[:, :, 3] = (shadow_alpha * 255.0).astype(np.uint8)
            shadow_img = Image.fromarray(shadow_rgba, mode="RGBA")
            
            # 2. Construct Product Body Layer (RGBA) — kept CRISP (no feathering) so the
            # product never looks cut-out/pasted. For a cut-off base this keeps the bottom a
            # clean straight edge that bleeds off-canvas, instead of a faded "cutout" edge.
            product_rgba = np.zeros((h_c, w_c, 4), dtype=np.uint8)
            product_rgba[:, :, :3] = np.round(arr_crop).astype(np.uint8)
            product_rgba[:, :, 3] = (product_mask.astype(np.float32) * 255.0).astype(np.uint8)
            product_img = Image.fromarray(product_rgba, mode="RGBA")

        # Scaling factor: Use Slot 1 scale factor exactly if cached
        cached_scale = sku_scale or self.scale_cache.get(sku)
        
        if cached_scale is not None:
            scale = cached_scale
        else:
            # Calculate scale based on targets
            scale_w = (target_w * self.target_size) / W_p
            scale_h = (target_h * self.target_size) / H_p
            scale = min(scale_w, scale_h)
            
            # Apply safety limits only for the main view calculation
            if W_p * scale > 1900.0:
                scale = 1900.0 / W_p
                
            if is_centered:
                if H_p * scale > 1900.0:
                    scale = 1900.0 / H_p
            else:
                max_h_allowed = int(self.target_size - (floor_pct * self.target_size) - 50)
                if H_p * scale > max_h_allowed:
                    scale = max_h_allowed / H_p
        
        # Cache the scale factor if it was newly calculated
        if sku not in self.scale_cache:
            self.scale_cache[sku] = scale
            
        # Apply scaling to the layers (product + shadow)
        new_w_crop = int(w_c * scale)
        new_h_crop = int(h_c * scale)
        
        resized_shadow = shadow_img.resize((new_w_crop, new_h_crop), Image.Resampling.LANCZOS)
        resized_product = product_img.resize((new_w_crop, new_h_crop), Image.Resampling.LANCZOS)
        
        if preserve_original:
            # Scale-aware, dynamic edge fading: gently fade out the outer edges of the crop box to pure white.
            # This completely eliminates any sharp transition lines, off-white background borders, or JPEG/resizing artifacts.
            # We bound the fade width dynamically to at most 40% of the scaled padding to ensure we never touch the product body.
            arr_resized = np.array(resized_product).astype(np.float32)
            h_r, w_r, _ = arr_resized.shape
            
            fade_w = min(15, max(1, int(pad_x * scale * 0.4)))
            fade_h_top = min(15, max(1, int(pad_top * scale * 0.4)))
            fade_h_bottom = min(15, max(1, int(pad_bottom * scale * 0.4)))
            
            if fade_w > 0 and fade_h_top > 0 and fade_h_bottom > 0:
                grad_x = np.clip(np.arange(w_r, dtype=np.float32) / fade_w, 0.0, 1.0)
                grad_x = np.minimum(grad_x, np.clip((w_r - 1 - np.arange(w_r, dtype=np.float32)) / fade_w, 0.0, 1.0))
                
                y_coords = np.arange(h_r, dtype=np.float32)
                grad_y_top = np.clip(y_coords / fade_h_top, 0.0, 1.0)
                
                if not is_cutoff_base:
                    grad_y_bottom = np.clip((h_r - 1 - y_coords) / fade_h_bottom, 0.0, 1.0)
                    grad_y = np.minimum(grad_y_top, grad_y_bottom)
                else:
                    grad_y = grad_y_top
                    
                crop_mask = np.outer(grad_y, grad_x)
                pull_white = 1.0 - crop_mask
                pull_3d = np.expand_dims(pull_white, axis=-1)
                
                # Blend the RGB channels smoothly to pure white (255, 255, 255)
                white_img = np.ones_like(arr_resized[:, :, :3]) * 255.0
                arr_resized[:, :, :3] = arr_resized[:, :, :3] * (1.0 - pull_3d) + white_img * pull_3d
                
                resized_product = Image.fromarray(np.round(arr_resized).astype(np.uint8), mode="RGBA")
        
        # Body-Centric Translation Calculations using visual upper mass bounds
        x_min_vis, x_max_vis = self.get_visual_body_bounds(img, bbox_clean, category)
        W_vis = max(1.0, float(x_max_vis - x_min_vis))
        
        new_w_vis = int(W_vis * scale)
        new_h_body = int(H_p * scale)
        
        paste_x_body = (self.target_size - new_w_vis) // 2
        if category == "lamp_pendant":
            # Pendant lamp: top-aligned, hanging from Y=80px (4% of canvas) to look natural and not float centered
            paste_y_body = 80
        elif is_centered:
            # Center-aligned Y
            paste_y_body = (self.target_size - new_h_body) // 2
        else:
            # Floor-aligned Y: ground exactly at Y=2000px if cutoff base, otherwise Y=1800px (floor_pct = 0.10)
            current_floor_pct = 0.0 if is_cutoff_base else 0.10
            paste_y_body = int(self.target_size - (current_floor_pct * self.target_size) - new_h_body)
            
        # Offset the paste coordinates of the crop based on where the visual body sits inside it
        offset_x = x_min_vis - crop_x_min
        offset_y = y_min_clean - crop_y_min
        
        paste_x = paste_x_body - int(offset_x * scale) + adjust_x
        paste_y = paste_y_body - int(offset_y * scale) + adjust_y
        
        # Enforce Bottom & Top Clipping Guards for the product body
        body_y_min = paste_y_body + adjust_y
        body_y_max = body_y_min + new_h_body
        
        # Increase limits to 35px to guarantee the product body stays away from borders
        bottom_limit = self.target_size if is_cutoff_base else (self.target_size - 35)
        top_limit = 35
        
        if body_y_max > bottom_limit:
            shift_up = body_y_max - bottom_limit
            paste_y_body -= shift_up
            paste_y -= shift_up
            body_y_min -= shift_up
            body_y_max -= shift_up
            
        if body_y_min < top_limit:
            if new_h_body <= (bottom_limit - top_limit):
                shift_down = top_limit - body_y_min
                paste_y_body += shift_down
                paste_y += shift_down
                body_y_min += shift_down
                body_y_max += shift_down

        # Enforce Left & Right Clipping Guards for the product body
        body_x_min = paste_x_body + adjust_x
        body_x_max = body_x_min + new_w_vis
        left_limit = 35
        right_limit = self.target_size - 35
        
        if body_x_max > right_limit:
            shift_left = body_x_max - right_limit
            paste_x -= shift_left
            body_x_min -= shift_left
            body_x_max -= shift_left
            
        if body_x_min < left_limit:
            if new_w_vis <= (right_limit - left_limit):
                shift_right = left_limit - body_x_min
                paste_x += shift_right
        
        # Canvas Composition
        canvas = Image.new("RGBA", (self.target_size, self.target_size), (255, 255, 255, 255))
        # Paste transparent shadow layer
        canvas.paste(resized_shadow, (paste_x, paste_y), mask=resized_shadow)
        # Paste transparent product layer on top
        canvas.paste(resized_product, (paste_x, paste_y), mask=resized_product)
        # Convert back to RGB for output compatibility
        canvas = canvas.convert("RGB")
        
        # Smooth Canvas Border Feathering: gently fade the outer 30px to white so any
        # shadow that runs to the canvas edge DISSOLVES into the white background instead
        # of being chopped with a hard line. For a cut-off base the product is meant to
        # bleed off the bottom, so the bottom edge is left untouched.
        # We apply this edge-cleaning globally to BOTH paths to ensure absolutely 0% black seams,
        # border artifacts, or compression/JPEG noise in the shop.
        feather_width = 30
        arr = np.array(canvas).astype(np.float32)
        h_arr, w_arr, _ = arr.shape
        
        x = np.arange(w_arr, dtype=np.float32)
        y = np.arange(h_arr, dtype=np.float32)
        
        dist_x = np.minimum(x, w_arr - 1.0 - x)
        if is_cutoff_base:
            dist_y = y                          # feather toward the top only; keep bottom intact
        else:
            dist_y = np.minimum(y, h_arr - 1.0 - y)
        
        grid_x, grid_y = np.meshgrid(dist_x, dist_y)
        dist = np.minimum(grid_x, grid_y)
        
        alpha = np.clip(dist / feather_width, 0.0, 1.0) ** 2
        alpha_3d = np.expand_dims(alpha, axis=-1)
        
        white = np.ones_like(arr) * 255.0
        blended = arr * alpha_3d + white * (1.0 - alpha_3d)
        canvas = Image.fromarray(np.round(blended).astype(np.uint8))

        # Force the outer 32px border to absolutely pure white for a clean webshop
        # background. The bottom border is skipped for cut-off bases so the grounded
        # product/shadow is not sliced by a white strip.
        # Using 32px aligns with 16x16 JPEG macroblock boundaries, preventing chroma bleed.
        b = 32
        arr_final = np.array(canvas)
        arr_final[0:b, :, :] = 255
        arr_final[:, 0:b, :] = 255
        arr_final[:, -b:, :] = 255
        if not is_cutoff_base:
            arr_final[-b:, :, :] = 255
        canvas = Image.fromarray(arr_final)
        
        shadow_img.close()
        product_img.close()
        resized_shadow.close()
        resized_product.close()
        
        return canvas, scale, (crop_x_min, crop_y_min, crop_x_max, crop_y_max), (paste_x, paste_y)
