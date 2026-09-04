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