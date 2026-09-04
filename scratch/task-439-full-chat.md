### TYPE: ASSISTANT (2026-06-17T09:52:11.396Z)

Jag börjar med att läsa in den relevanta koden så att mina ändringar matchar befintlig stil och struktur. Låt mig hämta filerna parallellt.

---

### TYPE: ASSISTANT (2026-06-17T09:52:20.454Z)

Nu läser jag QA-modulerna, decolorization och stödfiler (local_vlm, config) för att förstå hela kedjan.

---

### TYPE: ASSISTANT (2026-06-17T09:52:32.495Z)

Nu läser jag stödfilerna för att förstå GPU-kontentionen och hur Florence-2 laddas/lossas, samt konfig och tester.

---

### TYPE: ASSISTANT (2026-06-17T09:52:40.943Z)

Låt mig läsa de befintliga testerna och de scratch-skript som rör skuggor/centrering, för att matcha konventioner och förstå vad som redan testats.

---

### TYPE: ASSISTANT (2026-06-17T10:05:18.710Z)

Jag har läst igenom hela kedjan (`composition.py`, `classification.py`, `orchestrator.py`, `qa_loop.py`, `qa_checker.py`, `decolorization.py`, `local_vlm.py`, `config.py` samt befintliga tester). Nedan följer mitt arkitektbeslut för Fråga 1 och de exakta kodändringarna.

> Notera: jag kör read-only enligt loop-kontraktet, så detta är *förslag* i form av exakta ersättningsblock — precis det format orkestrator-agenten kan applicera direkt som en changeset.

---

## Fråga 1 — GPU-kontention i Stage 3 (arkitektbeslut)

**Rotorsak:** Stage 3 startar en `ProcessPoolExecutor` med upp till 8 processer. Varje arbetare kör QA-loopen, vars **Tier 2** anropar `run_local_florence2_qa` → `local_vlm.get_florence2_model()` som laddar Florence‑2 på **CUDA**. 8 processer som samtidigt laddar in en modell på *ett* GPU ger VRAM-utmattning, CUDA‑OOM och icke-deterministiska krascher.

**Beslut (Alternativ C, härdad):** Lokal Florence‑QA (Tier 2) **inaktiveras helt i CPU-poolen**. GPU‑arbete reserveras för den dedikerade, serialiserade Stage 2. När Tier 1‑heuristiken fäller ett utfall faller vi direkt igenom till den **processäkra moln-baserade Gemini-tie-breakern (Tier 3)**. Detta är mest robust eftersom (a) det eliminerar all GPU-kontention by design, (b) Tier 3 redan finns och är ren HTTP, och (c) Tier 1 + relaxade trösklar (se nedan) minskar falska utfall så att tie-breakern sällan behövs.

Implementeras via en explicit flagga `allow_local_gpu_qa` (default `False`) som trådas genom QA-loopen; CPU-arbetaren skickar alltid `False`.

## Fråga 2 — Skuggkanter

Princip: skuggan får löpa utanför ramen (naturlig beskärning), men **våra beskärningar får aldrig införa konstgjorda kanter**. Konkret: (1) produkten feathras *aldrig* (det är den som ser "urklippt" ut), (2) skuggan får en mjuk **rollover/falloff** så att en hård linje aldrig uppstår — men med så generös padding att rollovern normalt landar i vitt och blir osynlig, (3) vid cut-off-bas bevaras kontaktskuggan ända ner, (4) decolorization vitnar bara *redan nästan-vita* kantpixlar (rör inte äkta skugga).

---

# 1. `reforma-turboflow/reforma_pipeline/composition.py`

### Block 1 — Adaptiv skuggpadding (ersätt rad 160–167)

```python
        # Crop box includes shadow + padding margins (40px horizontal, 20px vertical)
        crop_x_min = max(0, x_min_raw - 40)
        crop_y_min = max(0, y_min_raw - 20)
        crop_x_max = min(w, x_max_raw + 40)
        crop_y_max = min(h, y_max_raw + 20)
        
        cropped_area = img.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
        w_c, h_c = cropped_area.size
```

**MED:**

```python
        # Crop box includes the shadow plus an ADAPTIVE white margin. The margin is sized
        # relative to the image so the crop boundary lands in genuinely white space (where
        # the shadow's natural alpha has already decayed to ~0). Extra room is reserved
        # below the product to hold the contact/cast shadow's natural rollover. This is
        # what lets us "crop the image as it is" without the shadow meeting a hard line.
        longest_side = float(max(w, h))
        pad_x = max(40, int(0.035 * longest_side))
        pad_top = max(20, int(0.035 * longest_side))
        pad_bottom = max(40, int(0.07 * longest_side))
        crop_x_min = max(0, x_min_raw - pad_x)
        crop_y_min = max(0, y_min_raw - pad_top)
        crop_x_max = min(w, x_max_raw + pad_x)
        crop_y_max = min(h, y_max_raw + pad_bottom)
        
        cropped_area = img.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
        w_c, h_c = cropped_area.size
```

### Block 2 — Rollover på skuggan, krispig produkt, bevarad skugga (ersätt rad 188–220)

```python
        # Calculate soft edge feathering mask (vignette outer 20px)
        feather = 20
        vignette_mask = np.ones((h_c, w_c), dtype=np.float32)
        if w_c > 2 * feather and h_c > 2 * feather:
            grad_x = np.clip(np.arange(w_c, dtype=np.float32) / feather, 0.0, 1.0)
            grad_x = np.minimum(grad_x, np.clip((w_c - 1 - np.arange(w_c, dtype=np.float32)) / feather, 0.0, 1.0))
            grad_y = np.clip(np.arange(h_c, dtype=np.float32) / feather, 0.0, 1.0)
            grad_y = np.minimum(grad_y, np.clip((h_c - 1 - np.arange(h_c, dtype=np.float32)) / feather, 0.0, 1.0))
            vignette_mask = np.outer(grad_y, grad_x)
            
        # 1. Construct Shadow Alpha Layer (ACSS)
        # Alpha = 1.0 - (Luma / 255.0). Pure black color is used to represent the shadow.
        shadow_alpha = 1.0 - (luma / 255.0)
        # Apply 0.95 threshold clipping (if pixel is nearly white, force Alpha = 0.0)
        shadow_alpha[luma / 255.0 > 0.95] = 0.0
        # Exclude the product body pixels from the shadow alpha layer to avoid double-layering
        shadow_alpha[product_mask] = 0.0
        # Apply feathering mask
        shadow_alpha = np.clip(shadow_alpha * vignette_mask, 0.0, 1.0)
        
        # Build transparent Shadow Layer (RGBA)
        shadow_rgba = np.zeros((h_c, w_c, 4), dtype=np.uint8)
        # RGB = (0,0,0) (neutral black)
        # A = calculated alpha
        shadow_rgba[:, :, 3] = (shadow_alpha * 255.0).astype(np.uint8)
        shadow_img = Image.fromarray(shadow_rgba, mode="RGBA")
        
        # 2. Construct Product Body Layer (RGBA)
        product_rgba = np.zeros((h_c, w_c, 4), dtype=np.uint8)
        product_rgba[:, :, :3] = np.round(arr_crop).astype(np.uint8)
        product_mask_alpha = np.clip(product_mask.astype(np.float32) * vignette_mask, 0.0, 1.0)
        product_rgba[:, :, 3] = (product_mask_alpha * 255.0).astype(np.uint8)
        product_img = Image.fromarray(product_rgba, mode="RGBA")
```

**MED:**

```python
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

        # 1. Construct Shadow Alpha Layer (ACSS)
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
```

### Block 3 — Canvas-feather som inte kapar skuggor (ersätt rad 330–357)

```python
        # Smooth Canvas Border Feathering: Gradually fade the outer 80px to white
        feather_width = 80
        arr = np.array(canvas).astype(np.float32)
        h_arr, w_arr, _ = arr.shape
        
        x = np.arange(w_arr, dtype=np.float32)
        y = np.arange(h_arr, dtype=np.float32)
        
        dist_x = np.minimum(x, w_arr - 1.0 - x)
        dist_y = np.minimum(y, h_arr - 1.0 - y)
        
        grid_x, grid_y = np.meshgrid(dist_x, dist_y)
        dist = np.minimum(grid_x, grid_y)
        
        alpha = np.clip(dist / feather_width, 0.0, 1.0) ** 2
        alpha_3d = np.expand_dims(alpha, axis=-1)
        
        white = np.ones_like(arr) * 255.0
        blended = arr * alpha_3d + white * (1.0 - alpha_3d)
        canvas = Image.fromarray(np.round(blended).astype(np.uint8))

        # Force the outer 15px border of the canvas to be absolutely pure white (#FFFFFF)
        arr_final = np.array(canvas)
        arr_final[0:15, :, :] = 255
        arr_final[-15:, :, :] = 255
        arr_final[:, 0:15, :] = 255
        arr_final[:, -15:, :] = 255
        canvas = Image.fromarray(arr_final)
```

**MED:**

```python
        # Smooth Canvas Border Feathering: gently fade the outer 80px to white so any
        # shadow that runs to the canvas edge DISSOLVES into the white background instead
        # of being chopped with a hard line. For a cut-off base the product is meant to
        # bleed off the bottom, so the bottom edge is left untouched.
        feather_width = 80
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

        # Force the outer 15px border to absolutely pure white for a clean webshop
        # background. The bottom border is skipped for cut-off bases so the grounded
        # product/shadow is not sliced by a white strip.
        arr_final = np.array(canvas)
        arr_final[0:15, :, :] = 255
        arr_final[:, 0:15, :] = 255
        arr_final[:, -15:, :] = 255
        if not is_cutoff_base:
            arr_final[-15:, :, :] = 255
        canvas = Image.fromarray(arr_final)
```

---

# 2. `reforma-turboflow/reforma_pipeline/decolorization.py`

### Grindad kant-vinjett som bevarar skugga (ersätt rad 40–59)

```python
    # Apply soft vignette-fade to pure white at the outer 5% edges
    h, w, _ = final_arr.shape
    vignette = 0.05
    edge_w = int(w * vignette)
    edge_h = int(h * vignette)
    
    if edge_w > 0 and edge_h > 0:
        grad_x = np.clip(np.arange(w, dtype=np.float32) / edge_w, 0.0, 1.0)
        grad_x = np.minimum(grad_x, np.clip((w - 1 - np.arange(w, dtype=np.float32)) / edge_w, 0.0, 1.0))
        
        grad_y = np.clip(np.arange(h, dtype=np.float32) / edge_h, 0.0, 1.0)
        grad_y = np.minimum(grad_y, np.clip((h - 1 - np.arange(h, dtype=np.float32)) / edge_h, 0.0, 1.0))
        
        vignette_mask = np.outer(grad_y, grad_x)
        vignette_mask_3d = np.expand_dims(vignette_mask, axis=-1)
        
        white_img = np.ones_like(final_arr) * 255.0
        final_arr = final_arr * vignette_mask_3d + white_img * (1.0 - vignette_mask_3d)
        
    return Image.fromarray(np.round(final_arr).astype(np.uint8))
```

**MED:**

```python
    # Apply a soft vignette-fade to pure white at the outer 5% edges, but ONLY pull pixels
    # that are already near-white toward white. This cleans up off-white corner gradients/
    # dirt WITHOUT artificially fading genuine shadows that legitimately reach the frame
    # edge — the webshop accepts a shadow running off-frame, but it must look like a
    # natural crop, not a faded "cut-out" edge.
    h, w, _ = final_arr.shape
    vignette = 0.05
    edge_w = int(w * vignette)
    edge_h = int(h * vignette)
    
    if edge_w > 0 and edge_h > 0:
        grad_x = np.clip(np.arange(w, dtype=np.float32) / edge_w, 0.0, 1.0)
        grad_x = np.minimum(grad_x, np.clip((w - 1 - np.arange(w, dtype=np.float32)) / edge_w, 0.0, 1.0))
        
        grad_y = np.clip(np.arange(h, dtype=np.float32) / edge_h, 0.0, 1.0)
        grad_y = np.minimum(grad_y, np.clip((h - 1 - np.arange(h, dtype=np.float32)) / edge_h, 0.0, 1.0))
        
        vignette_mask = np.outer(grad_y, grad_x)        # 1.0 = keep, 0.0 = pull to white
        pull_to_white = 1.0 - vignette_mask
        
        # Gate the whitening so it only affects near-white pixels; real shadow/product
        # pixels (luma < 225) are left completely untouched.
        luma_final = 0.299 * final_arr[:, :, 0] + 0.587 * final_arr[:, :, 1] + 0.114 * final_arr[:, :, 2]
        near_white = np.clip((luma_final - 225.0) / 20.0, 0.0, 1.0)  # 0 below 225, 1 at/above 245
        pull_to_white = pull_to_white * near_white
        pull_3d = np.expand_dims(pull_to_white, axis=-1)
        
        white_img = np.ones_like(final_arr) * 255.0
        final_arr = final_arr * (1.0 - pull_3d) + white_img * pull_3d
        
    return Image.fromarray(np.round(final_arr).astype(np.uint8))
```

---

# 3. `reforma-turboflow/reforma_pipeline/classification.py`

### 3a. Ny cachad zoom-resolver (lägg till direkt efter `query_gemini_for_zoom_status`, dvs efter rad 335)

```python
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
```

### 3b. Låt `is_zoom_or_sketch` använda resolvern (ersätt rad 533–548)

```python
    # If sketch or margin-touch triggers, query Gemini (with cache) to verify
    if is_sketch_candidate or is_margin_touch_candidate:
        cache_key = f"zoom_{img_key}"
        if cache_key in cache:
            return cache[cache_key]
        elif gemini_key:
            res = query_gemini_for_zoom_status(img_path, gemini_key)
            if res is not None:
                cache[cache_key] = res
                return res
            else:
                return False
        else:
            return False

    return False
```

**MED:**

```python
    # If sketch or margin-touch triggers, confirm via the cached zoom-status helper
    # (queries Gemini at most once per image and stores the verdict in the cache).
    if is_sketch_candidate or is_margin_touch_candidate:
        res = resolve_zoom_status(img_path, img_key, gemini_key, cache=cache)
        return bool(res) if res is not None else False

    return False
```

---

# 4. `reforma-turboflow/reforma_pipeline/orchestrator.py`

### 4a. Importera resolvern (ersätt rad 25–29)

```python
from reforma_pipeline.classification import (
    load_gemini_key, normalize_name, classify_and_size_product, adjust_size_by_name,
    classify_image_type_robust, query_gemini_for_zoom_status, classify_image_semantics_robust,
    is_zoom_or_sketch, query_gemini_batch_for_sku
)
```

**MED:**

```python
from reforma_pipeline.classification import (
    load_gemini_key, normalize_name, classify_and_size_product, adjust_size_by_name,
    classify_image_type_robust, query_gemini_for_zoom_status, classify_image_semantics_robust,
    is_zoom_or_sketch, query_gemini_batch_for_sku, resolve_zoom_status
)
```

### 4b. Stage 3 — no-bbox-armen (bryter catch-22), ersätt rad 247–266

```python
        elif is_studio:
            # Fallback: if is_studio but no detections in bbox_data, query Gemini to confirm if it's a detail/zoom view
            local_cache = load_cache()
            cache_key = f"zoom_{img_key}"
            is_zoom_confirm = False
            if cache_key in local_cache:
                is_zoom_confirm = local_cache[cache_key]
            else:
                g_key = load_gemini_key()
                if g_key:
                    res = query_gemini_for_zoom_status(img_path, g_key)
                    if res is not None:
                        is_zoom_confirm = res
                        try:
                            latest_cache = load_cache()
                            latest_cache[cache_key] = res
                            save_cache(latest_cache)
                        except Ex

---

### TYPE: ASSISTANT (2026-06-17T10:06:43.610Z)

**MED:**

```python
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
```

### 4c. Stage 3 — auktoritativ zoom-override (ersätt rad 297–320)

```python
            if is_large_closeup or touches_sides or touches_tb or touches_top or touches_left or touches_right:
                # If it touches at least 3 margins, it is unconditionally a zoom view
                num_touches = sum([touches_left, touches_right, touches_top, touches_bottom])
                if num_touches >= 3:
                    is_zoom_confirm = True
                else:
                    local_cache = load_cache()
                    cache_key = f"zoom_{img_key}"
                    is_zoom_confirm = False
                    if cache_key in local_cache:
                        is_zoom_confirm = local_cache[cache_key]
                    else:
                        g_key = load_gemini_key()
                        if g_key:
                            res = query_gemini_for_zoom_status(img_path, g_key)
                            if res is not None:
                                is_zoom_confirm = res
                                try:
                                    latest_cache = load_cache()
                                    latest_cache[cache_key] = res
                                    save_cache(latest_cache)
                                except Exception as ce:
                                    print(f"  [Classifier Warning] Failed to save cache in CPU worker: {ce}")
                is_zoom_view = is_zoom_view or is_zoom_confirm
```

**MED:**

```python
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
```

### 4d. GPU-säker QA-anrop (ersätt slutet av anropet, rad 446–448)

```python
                    gemini_key=load_gemini_key(),
                    is_from_fix_folder=is_from_fix_folder
                )
```

**MED:**

```python
                    gemini_key=load_gemini_key(),
                    is_from_fix_folder=is_from_fix_folder,
                    allow_local_gpu_qa=False  # GPU-säkert: ingen lokal Florence-2 i CPU-poolen (Stage 3)
                )
```

Nästa del (Stage 4-auditen) kommer i ett eget block eftersom det är en hel funktion.

### 4e. Stage 4 — självläkande audit (ersätt hela `audit_zoom_outputs`, rad 524–565)

```python
def audit_zoom_outputs(curated_skus, zoom_dir):
    print("\n--- STAGE 4: Auditing Zoom Output Dimensions ---")
    audit_failures = 0
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
            
            if os.path.exists(zoom_path):
                if (is_studio or has_white_bg) and not is_zoom_view:
                    try:
                        with Image.open(zoom_path) as img:
                            w, h = img.size
                        if w != h:
                            print(f"  [Audit Failure] SKU {sku} Slot {slot} is non-square ({w}x{h}) but is classified as a studio full-view (is_studio={is_studio}, has_white_bg={has_white_bg}, is_zoom_view={is_zoom_view}).")
                            os.makedirs("scratch", exist_ok=True)
                            failure_info = {
                                "sku": sku,
                                "slot": slot,
                                "zoom_dest": os.path.abspath(zoom_path),
                                "error": f"Non-square studio full-view output: {w}x{h}"
                            }
                            failure_file = f"scratch/qa_failure_{sku}_audit.json"
                            with open(failure_file, 'w', encoding='utf-8') as f_fail:
                                json.dump(failure_info, f_fail, indent=2)
                            audit_failures += 1
                            break  # Move to next SKU
                    except Exception as e:
                        print(f"  [Audit Warning] Failed to inspect image {zoom_path}: {e}")
    print(f"Audit complete. Found {audit_failures} non-square studio zoom output failures.")
    return audit_failures
```

**MED:**

```python
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
            if not ((is_studio or has_white_bg) and not is_zoom_view):
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
```

De befintliga anropen (`audit_zoom_outputs([curated_data], zoom_dir)` på rad 981 och `audit_zoom_outputs(curated_skus, zoom_dir)` på rad 1133) fungerar oförändrat eftersom `self_heal=True` är default.

---

# 5. `reforma-turboflow/reforma_pipeline/qa_loop.py`

### 5a. Lägg till flaggan i signaturen (ersätt rad 68–69)

```python
        gemini_key: Optional[str] = None,
        is_from_fix_folder: bool = False
    ) -> Tuple[Image.Image, float, bool]:
```

**MED:**

```python
        gemini_key: Optional[str] = None,
        is_from_fix_folder: bool = False,
        allow_local_gpu_qa: bool = False
    ) -> Tuple[Image.Image, float, bool]:
```

### 5b. Grinda Tier 2 (Florence) bakom flaggan (ersätt rad 155–172)

```python
            else:
                # --- Tier 2: Local Florence-2 Object Layout Audit ---
                # We query Florence-2 to see if it agrees with the heuristic failures.
                # Since neural object localization is less sensitive to asymmetric shapes/noise,
                # if Florence-2 says centering and grounding are OK, we override Tier 1.
                print(f"  [QA Loop] Tier 1 failed: {qa_res['errors']}. Proceeding to Tier 2 (Florence-2)...")
                florence_qa = self.qa_checker.run_local_florence2_qa(
                    canvas=canvas,
                    target_floor=target_floor,
                    category=category
                )
                
                if florence_qa["passed"]:
                    print(f"  [QA Loop] Tier 2 (Florence-2) approved the layout. Overriding Tier 1 heuristic errors: {qa_res['errors']}")
                    qa_res["passed"] = True
                    qa_res["errors"] = []
                else:
                    print(f"  [QA Loop] Tier 2 failed: {florence_qa['errors']}")
```

**MED:**

```python
            else:
                # --- Tier 2: Local Florence-2 Object Layout Audit (GPU) ---
                # GPU-contention guard: Florence-2 lives on CUDA and Stage 3 runs as a
                # parallel CPU pool. Loading it from many workers at once thrashes/OOMs the
                # single GPU, so Tier 2 is DISABLED in the pool (allow_local_gpu_qa is False
                # there). We fall straight through to the process-safe cloud Gemini
                # tie-breaker (Tier 3). Florence-2 stays reserved for the dedicated,
                # serialized Stage 2 GPU stage.
                florence_qa = {"passed": False, "errors": []}
                if allow_local_gpu_qa:
                    print(f"  [QA Loop] Tier 1 failed: {qa_res['errors']}. Proceeding to Tier 2 (Florence-2)...")
                    florence_qa = self.qa_checker.run_local_florence2_qa(
                        canvas=canvas,
                        target_floor=target_floor,
                        category=category
                    )
                    if florence_qa["passed"]:
                        print(f"  [QA Loop] Tier 2 (Florence-2) approved the layout. Overriding Tier 1 heuristic errors: {qa_res['errors']}")
                        qa_res["passed"] = True
                        qa_res["errors"] = []
                    else:
                        print(f"  [QA Loop] Tier 2 failed: {florence_qa['errors']}")
                else:
                    print(f"  [QA Loop] Tier 1 failed: {qa_res['errors']}. Skipping local Florence-2 (Tier 2) "
                          f"under the CPU pool; deferring to cloud Gemini (Tier 3).")
```

Tier 3-blocket nedanför är oförändrat — det fungerar med `florence_qa = {"passed": False, "errors": []}` eftersom filtren faller tillbaka på Tier 1-heuristiken (`qa_res`).

### 5c. Skonsam decolorization-justering som bevarar skugga (ersätt rad 245–247)

```python
            # If background purity or halo leakage failed, adjust decolorization params
            if "BackgroundPurityError" in errors_str or "HaloLeakageError" in errors_str:
                slot_override["tolerance"] = float(min(35.0, slot_override.get("tolerance", 15.0) + 5.0))
                slot_override["blend_range"] = float(min(150.0, slot_override.get("blend_range", 80.0) + 10.0))
```

**MED:**

```python
            # If background purity or halo leakage failed, NUDGE decolorization gently and
            # cap it low: aggressive cleanup would desaturate/erase the natural shadow we
            # are now deliberately preserving. Prefer widening the blend over raising
            # tolerance.
            if "BackgroundPurityError" in errors_str or "HaloLeakageError" in errors_str:
                slot_override["tolerance"] = float(min(22.0, slot_override.get("tolerance", 15.0) + 3.0))
                slot_override["blend_range"] = float(min(120.0, slot_override.get("blend_range", 80.0) + 8.0))
```

---

# 6. `reforma-turboflow/reforma_pipeline/qa_checker.py`

### 6a. Skonsammare bakgrundsrenhet (ersätt rad 214–217)

```python
        # Count pixels that are NOT pure white/off-white (allow values >= 250 for soft shadows/compression)
        non_white_bg_count = np.sum(np.any(bg_pixels < 250, axis=-1))
        # Allow up to 10 pixels of tolerance for compression/edge noise
        bg_purity_passed = (non_white_bg_count <= 10)
```

**MED:**

```python
        # Count pixels that are NOT pure white/off-white (allow values >= 250 for soft shadows/compression)
        non_white_bg_count = np.sum(np.any(bg_pixels < 250, axis=-1))
        # Composition now guarantees a clean 15px white border, so any stray edge pixels
        # are only ever compression/anti-alias noise. Keep a small, forgiving tolerance so
        # a preserved shadow grazing the safe zone is never a hard failure.
        bg_purity_passed = (non_white_bg_count <= 20)
```

### 6b. Halo-check som inte straffar naturlig kontaktskugga (ersätt rad 301–318)

```python
        transition_mask = dilated_mask & ~body_mask
        transition_pixels = arr[transition_mask]
        
        halo_leakage_passed = True
        halo_pixel_count = 0
        ratio = 0.0

        if transition_pixels.size > 0:
            gray = 0.299 * transition_pixels[:, 0] + 0.587 * transition_pixels[:, 1] + 0.114 * transition_pixels[:, 2]
            near_white = (gray >= 250.0) & (gray < 255.0)
            is_warm = (transition_pixels[:, 0] > transition_pixels[:, 2] + 1)
            halo_pixel_count = np.sum(near_white & is_warm)
            body_pixel_count = np.sum(body_mask)

            if body_pixel_count > 0:
                ratio = float(halo_pixel_count) / body_pixel_count
                if ratio > 0.015:  # threshold 1.5%
                    halo_leakage_passed = False
```

**MED:**

```python
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
```

### 6c. Uppdatera felmeddelandets gräns (ersätt rad 335)

```python
            errors.append(f"HaloLeakageError: edge halo ratio is {ratio:.4f} ({halo_pixel_count} pixels, limit is 0.0050)")
```

**MED:**

```python
            errors.append(f"HaloLeakageError: edge halo ratio is {ratio:.4f} ({halo_pixel_count} pixels, limit is 0.0250)")
```

---

# Sammanfattning för orkestrator-agenten

| Fil | Ändringar |
|---|---|
| `composition.py` | Block 1 (adaptiv padding), Block 2 (smoothstep-rollover på skuggan, krispig produkt, top-only rollover vid cutoff), Block 3 (canvas-feather/vit kant hoppar över botten vid cutoff) |
| `decolorization.py` | Kant-vinjett grindad mot `near_white` → äkta skuggor bevaras |
| `classification.py` | Ny `resolve_zoom_status` (3a) + `is_zoom_or_sketch` använder den (3b) |
| `orchestrator.py` | Import (4a), Stage 3 no-bbox-arm (4b), Stage 3-override (4c), `allow_local_gpu_qa=False` (4d), självläkande Stage 4-audit (4e) |
| `qa_loop.py` | Ny flagga (5a), Tier 2 grindad bakom flaggan (5b), skonsam decolorization-bump (5c) |
| `qa_checker.py` | Skonsammare bakgrundsrenhet (6a), halo exkluderar kontaktskugga + relaxad tröskel (6b/6c) |

**Verifiering jag rekommenderar innan merge:**
- `tests/test_shadow_math.py` påverkas inte (ACSS-matematiken är oförändrad) — bör fortsatt vara grön.
- Kör en SKU med cut-off-bas (t.ex. soffa) och en med kontaktskugga (stol) genom Stage 3 och okulärbesiktiga: ingen fade-ring runt produkten, mjuk skuggkant, ren vit ram, ingen vit remsa under cut-off-basen.
- Bekräfta att Stage 3-poolen inte längre rör CUDA (sök i loggen efter `[VLM Manager] Loading` under Stage 3 — ska inte förekomma).

Två saker jag medvetet **inte** rörde, säg till om du vill ha dem: (1) jag behöll `run_local_florence2_qa` i `qa_checker.py` (den är ofarlig så länge `allow_local_gpu_qa=False` och kan återanvändas i en framtida serialiserad audit); (2) jag tog inte bort den bbox-beroende margin-heuristiken i `curate_sku` — den är redan skyddad av `img_key in bbox_db` och är därför vilande på första körningen, så catch-22:n bryts av no-bbox-armen (4b) + Stage 3-overriden (4c) utan att jag behöver röra curation-logiken.

---

