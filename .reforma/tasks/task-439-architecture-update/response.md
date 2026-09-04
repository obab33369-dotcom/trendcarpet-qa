The plan-file, interactive-question, and exit-plan tools are all disabled in this session (only read-only tools are enabled), so I'll deliver the complete Lead Architect design inline — which is the substance you asked for. I've made four design decisions myself (flagged below so you can override any of them).

---

# Reforma TurboFlow — Quality Fix Architecture

## What I found (current state)

Your three fixes are *partially* present but fragile and scattered:

- **`FORCE_ORIGINAL=1`** already exists (`composition.py:226`) and is set by `run_test_5.py`. When on, it pastes the whole crop as one solid RGBA layer and skips ACSS masking, the smoothstep rollover, and the canvas feathering/white-border. ✔️ but it's a *global* env var, and the solid paste **seams** if the crop background isn't already pure white.
- **`get_visual_body_bounds`** (`composition.py:40`) is an attempt at body-centric centering, but it searches the **full image width** (`arr[y_start:y_end, :, :]`) — so shadow pixels in the upper-body band leak into the center calculation. (`scratch/trace_visual_bounds.py` shows the team measuring exactly this center deviation.)
- **Padding** happens in **3+ places** (`orchestrator.py:341`, the QA-fail fallback at `:471`, and `audit_zoom_outputs` at `:547`), each re-deriving intent from `is_studio`/`has_white_bg`/`is_zoom_view`. A gray-bg close-up misclassified as studio gets padded → seam, and Stage 4 will *re-introduce* the seam even if you fix one site.

## Decisions (assumptions — override if needed)

1. **Shadow:** make `PRESERVE` the default per-image policy; **keep** ACSS as a fallback (don't delete).
2. **Centering:** SAM3 body bbox is authoritative; keep the seat/upper-mass refinement for chairs but **constrain the search to the bbox**.
3. **Zoom:** use the Reforma slot convention (8 & 10 = zoom) as a **strong prior** *and* gate padding on a **measured** near-white background (belt + suspenders).
4. **Verify:** offline `unittest` tests (matching your `reforma-turboflow/tests/` style) **plus** `run_test_5.py` end-to-end.

---

## 1. Architecture: one explicit per-image `RenderProfile`

Replace the scattered booleans + global env var with a single policy object decided **once** in `curate_sku`, carried in `processed_slots[slot]["profile"]`, and consumed everywhere (composition, qa_loop, audit). Additive and reversible — existing booleans stay; new function params default to env-resolution so `FORCE_ORIGINAL=1` keeps working unchanged.

```python
# reforma_pipeline/render_profile.py  (or top of composition.py)
from dataclasses import dataclass

@dataclass
class RenderProfile:
    slot: int
    render_mode: str       # "hero_square" | "zoom_rect" | "lifestyle_raw" | "sketch_square"
    shadow_policy: str      # "preserve" | "synthetic_acss"
    background_policy: str   # "passthrough" | "clean_offwhite"
    source_kind: str        # "white_bg_fix" | "topaz" | "original"
```

Decision rules in `curate_sku` (where `is_studio`/`is_zoom_view`/`has_white_bg` already exist):
- `render_mode`: `zoom_rect` if `is_zoom_view or slot in (8,10)`; else `lifestyle_raw` if not studio & not white-bg; else `sketch_square` if the sketch heuristic fires; else `hero_square`.
- `shadow_policy = "preserve"` by default (especially `white_bg_fix`); `"synthetic_acss"` only when explicitly configured.
- `background_policy = "passthrough"` for `white_bg_fix` (already #FFFFFF → keep shadow pixel-perfect); `"clean_offwhite"` otherwise.

This collapses the 3+ padding sites into one rule: *only `hero_square`/`sketch_square` are ever padded.*

---

## 2. Concrete code modifications

### Fix B — body-centric centering · `composition.py`

Constrain the horizontal search in `get_visual_body_bounds` to the SAM3 bbox x-range (replace the full-width slice at `:64-82`):

```python
        # CONSTRAIN search to the SAM3 body bbox: a floor/cast shadow outside the
        # furniture's physical x-extent can no longer pull the computed center.
        arr = np.array(img_cleaned.convert('RGB'))
        x_lo = max(0, min(w - 1, int(x_min_clean)))
        x_hi = max(x_lo + 1, min(w, int(x_max_clean)))
        band = arr[y_start:y_end, x_lo:x_hi, :]
        non_white_mask = np.sum(255 - band, axis=-1) > 15
        coords = np.argwhere(non_white_mask)
        if coords.size > 0:
            return int(coords[:, 1].min()) + x_lo, int(coords[:, 1].max()) + x_lo
        return int(x_min_clean), int(x_max_clean)
```

The downstream translation math (`:292-316`) is unchanged — the crop *still includes* the shadow (so it bleeds naturally); only the centering math now ignores it. Seat-centric chair logic is preserved.

**Required companion edit · `qa_checker.py:259-274`** — mirror the same constraint (slice the centering search to `[body_x_min_clip, body_x_max_clip]`). Without this, the QA loop re-measures center over the full width, pushes `adjust_x`, and oscillates against the fix.

### Fix A — preserve original shadow · `composition.py` + `orchestrator.py`

`composition.py` — add `shadow_policy: Optional[str] = None` to `compose_studio_image` (`:85`) and resolve `force_original` from profile *or* env (`:225-226`):

```python
        import os
        force_original = (shadow_policy == "preserve") or (os.environ.get("FORCE_ORIGINAL") == "1")
```

The existing `if force_original:` block (`:227-232`) and the `if not force_original:` guards (`:366-403`) already do the right thing — no further change.

`orchestrator.py` — fix the **inverted** fix-folder logic (`:393-397`) so the solid paste never seams:

```python
                preserve_shadow = os.environ.get("FORCE_ORIGINAL") == "1"  # or profile.shadow_policy=="preserve"
                src_is_fix = "refoma white background fix" in img_path.lower()
                is_from_fix_folder = src_is_fix
                if src_is_fix:
                    is_wb = False        # passthrough: retouched pure-white bg, keep shadow EXACT
                elif preserve_shadow:
                    is_wb = True         # clean off-white → pure white so the solid paste has no seam
                # else: keep measured is_wb (legacy ACSS path)
```

Rationale: white-bg-fix renders are already #FFFFFF (verified by `scratch/check_source_background.py`) → skip cleaning to stay pixel-perfect. Off-white/Topaz studio sources get cleaned to white first so the solid crop blends seamlessly.

### Fix C — zoom padding invalidation · `orchestrator.py`

1. **Slot prior** in `curate_sku` (after `is_zoom_view = is_zoom_or_sketch(...)`, `:845`):
```python
       if slot in (8, 10):          # Reforma Närbild/Detaljbild slots → never padded
           is_zoom_view = True
```
2. **Measured-white padding gate** — helper near the top, gate every pad site on it:
```python
   def _bg_is_pure_white(img_rgb, thresh=244):
       arr = np.array(img_rgb.convert('RGB'))
       patches = [arr[10:25,10:25], arr[10:25,-25:-10], arr[-25:-10,10:25], arr[-25:-10,-25:-10]]
       return all(float(np.mean(p)) >= thresh for p in patches)
```
   - Route 1 (`:341`): `do_pad = (is_studio or has_white_bg) and not is_zoom_view and _bg_is_pure_white(img_resized)` — reuse this single `do_pad` for the `normal`/`liten` square-vs-rect choice (`:350-356`).
   - QA-fail fallback (`:471`): add `and not is_zoom_view and _bg_is_pure_white(img_resized)`.
3. **Stage-4 audit** `audit_zoom_outputs` (`:528`): after the studio guard, add `if slot in (8, 10): continue` so it never re-pads a rectangular zoom.

---

## 3. Scalability / CUDA-OOM / Windows guidelines (RTX 3000 Ada, 8 GB)

- **All three fixes are CPU-only** numpy/PIL math — never add `import torch`/model loads into `composition.py` or the CPU-pool worker.
- **Keep the GPU contract:** `allow_local_gpu_qa=False` in `process_sku_cpu_worker` (`:428`) stays — the 8 GB GPU can't host N parallel Florence-2s. SAM3 remains serialized in Stage 2 and unloaded (`gc.collect()` + `torch.cuda.empty_cache()`) before the CPU pool spawns.
- **Windows `spawn`:** keep `torch` imports lazy (already only in `segment_sku_gpu`); make `RenderProfile` a plain dataclass/dict so it pickles cleanly across workers.
- **Memory:** the bbox-constrained band is *smaller* than the old full-width slice. Canvas stays 2000×2000×4 (~16 MB/worker); `num_workers = min(cpu_count, 8)` unchanged.
- **File locking:** keep `save_image_safe` (atomic temp→rename + retry); never `rmtree` OneDrive paths.

---

## 4. Verification

**Unit tests** (offline, no GPU/network) in `reforma-turboflow/tests/`, `unittest` style:
- `test_centering_ignores_shadow` — body block + shadow block *outside* the bbox → `get_visual_body_bounds` returns body x-range only; composed body within ±10px of x=1000.
- `test_zoom_rect_no_padding` — `is_zoom_view=True` → rectangular (longest side 2000, `w!=h`), no margins.
- `test_padding_gate_gray_bg` — `_bg_is_pure_white` False on gray → no pad.
- `test_slot_prior` — slots 8 & 10 resolve to zoom.
- `test_shadow_preserve_solid` — `shadow_policy="preserve"` → composed pixels match cropped source over body+shadow (no ACSS darkening).

Run: `python -m pytest -q reforma-turboflow/tests/`

**End-to-end:** `python reforma-turboflow/run_test_5.py` → review OneDrive `.../ftp_upload_test_5/...`:
- **A:** soft shadows intact, no gray-rectangle seam.
- **B:** body centered — use `scratch/trace_visual_bounds.py`, expect deviation `< 10px`.
- **C:** slot 8/10 stay rectangular (~1333×2000) with continuous bg; slot 1-4 stay square 2000×2000.

**Rollout order:** B (+ qa_checker) → A bg-policy → C → `run_test_5.py` → (optional) thread `RenderProfile.shadow_policy` to retire the env var.

---

⚠️ Note: I could not save this to the plan file or call `ExitPlanMode` — the `Write`, `AskUserQuestion`, and (presumably) `ExitPlanMode` tools are disabled in this session, so this design is delivered inline. **No files were modified.** When you're ready to implement, re-run me in a mode with edit tools enabled, or confirm the four decisions above and I'll proceed.