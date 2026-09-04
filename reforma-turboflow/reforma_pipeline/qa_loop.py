import json
import os
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple, Optional
from reforma_pipeline.composition import CompositionEngine
from reforma_pipeline.qa_checker import QAChecker

class IterativeQACoordinator:
    """
    Manages the self-correcting loop, applying overrides and running retries.
    Reads/writes to sku_composition_overrides.json.
    """

    def __init__(self, overrides_path: str = "scratch/sku_composition_overrides.json"):
        self.overrides_path = overrides_path
        self.qa_checker = QAChecker()
        self.max_retries = 3

    def load_overrides(self) -> Dict[str, Any]:
        if os.path.exists(self.overrides_path):
            try:
                with open(self.overrides_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _convert_numpy_types(self, obj):
        if isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(v) for v in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def save_overrides(self, overrides: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.overrides_path), exist_ok=True)
        try:
            clean_overrides = self._convert_numpy_types(overrides)
            with open(self.overrides_path, 'w', encoding='utf-8') as f:
                json.dump(clean_overrides, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  [QA Loop Warning] Failed to save overrides: {e}")


    def run_qa_and_correct(
        self,
        engine: CompositionEngine,
        img_cleaned_func,  # lambda function that takes (tolerance, blend_range) and returns cleaned image
        bbox_clean: Tuple[int, int, int, int],
        category: str,
        sku: str,
        slot: int,
        is_zoom_view: bool,
        bg_color: np.ndarray,
        target_w: float,
        target_h: float,
        floor_pct: float,
        is_centered: bool,
        sku_scale: Optional[float],
        gemini_key: Optional[str] = None,
        is_from_fix_folder: bool = False,
        allow_local_gpu_qa: bool = False
    ) -> Tuple[Image.Image, float, bool]:
        """
        Runs the iterative composition & check loop.
        Returns the finalized PIL Image, scale factor used, and whether it passed QA.
        """
        overrides = self.load_overrides()
        sku_key = sku
        slot_key = str(slot)

        # Initialize overrides for this slot if not exists
        sku_overrides = overrides.setdefault(sku_key, {})
        slot_override = sku_overrides.setdefault(slot_key, {
            "adjust_x": 0,
            "adjust_y": 0,
            "scale_factor_override": None,
            "tolerance": 15.0,
            "blend_range": 80.0
        })

        attempt = 0
        while attempt < self.max_retries:
            # 1. Clean the background with current overrides
            tol = slot_override.get("tolerance", 15.0)
            blend = slot_override.get("blend_range", 80.0)
            img_curr = img_cleaned_func(tol, blend)
            w_curr, h_curr = img_curr.size

            # Determine if base is cut off
            is_cutoff_base = False
            if bbox_clean is not None:
                _, _, _, y_max_clean = bbox_clean
                if y_max_clean >= h_curr - 10:
                    is_cutoff_base = True

            # 2. Compose canvas using current translation overrides
            adj_x = slot_override.get("adjust_x", 0)
            adj_y = slot_override.get("adjust_y", 0)
            scale_override = slot_override.get("scale_factor_override", None)

            canvas, scale_used, crop_box, paste_pos = engine.compose_studio_image(
                img=img_curr,
                bbox_clean=bbox_clean,
                category=category,
                sku=sku,
                slot=slot,
                is_zoom_view=is_zoom_view,
                bg_color=bg_color,
                target_w=target_w,
                target_h=target_h,
                floor_pct=floor_pct,
                is_centered=is_centered,
                sku_scale=scale_override or sku_scale,
                adjust_x=adj_x,
                adjust_y=adj_y
            )

            if is_zoom_view:
                # Detail views bypass QA grounding/centering checks
                img_curr.close()
                return canvas, scale_used, True

            # 4. Multi-Tier QA Check
            # --- Tier 1: Local Heuristic Diagnostics ---
            qa_res = self.qa_checker.run_diagnostics(
                canvas=canvas,
                bbox_clean=bbox_clean,
                crop_box=crop_box,
                paste_pos=paste_pos,
                scale=scale_used,
                is_cutoff_base=is_cutoff_base,
                is_centered=is_centered,
                category=category
            )

            # Filter out BackgroundPurityError and HaloLeakageError for fix folder images or when forcing original shadows
            if is_from_fix_folder or os.environ.get("FORCE_ORIGINAL") == "1":
                qa_res["errors"] = [err for err in qa_res["errors"] if "BackgroundPurityError" not in err and "HaloLeakageError" not in err]
                if not qa_res["errors"]:
                    qa_res["passed"] = True

            target_floor = 2000 if is_cutoff_base else 1800

            # Determine if Tier 1 passed with high confidence (no errors detected by heuristics)
            if qa_res["passed"]:
                print(f"  [QA Loop] SKU {sku} Slot {slot} passed Tier 1 (Heuristics) with 100% confidence.")
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
                    
                # --- Tier 3: Cloud Gemini Vision QA Audit (Conditional tie-breaker) ---
                if not qa_res["passed"] and gemini_key:
                    print(f"  [QA Loop] Tier 1 & 2 failed. Proceeding to Tier 3 (Gemini Vision QA tie-breaker)...")
                    gemini_qa_res = self.qa_checker.run_gemini_vision_qa(
                        canvas=canvas,
                        target_floor=target_floor,
                        gemini_key=gemini_key
                    )
                    
                    issues = gemini_qa_res.get("issues", [])
                    filtered_issues = []
                    for issue in issues:
                        if is_from_fix_folder and issue == "bad_cleanup":
                            continue  # Skip background purity check for designer retouched images
                        if issue == "off_grounding":
                            # Filter out off_grounding if GroundingError/Florence2OffGrounding is in errors
                            if any("GroundingError" in err for err in qa_res.get("errors", [])) or \
                               any("Florence2OffGrounding" in err for err in florence_qa.get("errors", [])):
                                filtered_issues.append(issue)
                        elif issue == "off_center":
                            # Filter out off_center if OffCenterWarning/Florence2OffCenter is in errors
                            if any("OffCenterWarning" in err for err in qa_res.get("errors", [])) or \
                               any("Florence2OffCenter" in err for err in florence_qa.get("errors", [])):
                                filtered_issues.append(issue)
                        else:
                            filtered_issues.append(issue)
                    
                    gemini_qa_res["issues"] = filtered_issues
                    if not filtered_issues:
                        gemini_qa_res["passed"] = True

                    if gemini_qa_res.get("passed", True):
                        print(f"  [QA Loop] Tier 3 (Gemini Vision) approved the composition. Overriding previous errors.")
                        qa_res["passed"] = True
                        qa_res["errors"] = []
                    else:
                        qa_res["passed"] = False
                        qa_res["errors"].extend([f"GeminiVision:{issue}" for issue in filtered_issues])
                        
                        sugg = gemini_qa_res.get("suggested_adjustments", {})
                        if sugg.get("scale_multiplier", 1.0) < 1.0:
                            qa_res["is_clipped"] = True
                        if sugg.get("increase_tolerance", False) and not is_from_fix_folder:
                            if "BackgroundPurityError" not in qa_res["errors"]:
                                qa_res["errors"].append("BackgroundPurityError")
                        if "off_center" in filtered_issues and sugg.get("shift_x", 0) != 0:
                            qa_res["adjustments"]["delta_x"] += int(sugg["shift_x"])
                        if "off_grounding" in filtered_issues and sugg.get("shift_y", 0) != 0:
                            qa_res["adjustments"]["delta_y"] += int(sugg["shift_y"])
                elif not qa_res["passed"] and not gemini_key:
                    # If Gemini key is not available, compile the errors from Florence-2 as well
                    qa_res["errors"].extend(florence_qa.get("errors", []))

            if qa_res["passed"]:
                if attempt > 0:
                    print(f"  [QA Loop] SKU {sku} Slot {slot} passed QA on attempt {attempt+1}!")
                img_curr.close()
                return canvas, scale_used, True

            # If failed, log and calculate corrections
            errors_str = ", ".join(qa_res["errors"])
            print(f"  [QA Loop] SKU {sku} Slot {slot} failed QA on attempt {attempt+1}: {errors_str}")

            adj = qa_res["adjustments"]
            is_clipped = qa_res["is_clipped"]
            
            # Apply adjustments to overrides
            slot_override["adjust_x"] = int(slot_override.get("adjust_x", 0) + adj["delta_x"])
            slot_override["adjust_y"] = int(slot_override.get("adjust_y", 0) + adj["delta_y"])

            # If background purity or halo leakage failed, NUDGE decolorization gently and
            # cap it low: aggressive cleanup would desaturate/erase the natural shadow we
            # are now deliberately preserving. Prefer widening the blend over raising
            # tolerance.
            if "BackgroundPurityError" in errors_str or "HaloLeakageError" in errors_str:
                slot_override["tolerance"] = float(min(22.0, slot_override.get("tolerance", 15.0) + 3.0))
                slot_override["blend_range"] = float(min(120.0, slot_override.get("blend_range", 80.0) + 8.0))

            # If clipping occurred, shrink scale factor to avoid control loop windup/overshoot
            if is_clipped:
                curr_scale = scale_override or scale_used
                slot_override["scale_factor_override"] = float(curr_scale * 0.93)
                slot_override["adjust_x"] = 0
                slot_override["adjust_y"] = 0
                print(f"  [QA Loop] Clipping detected, shrinking scale to {slot_override['scale_factor_override']:.4f} and resetting offsets.")

            # Save overrides to disk
            self.save_overrides(overrides)

            # Clean up current canvas
            canvas.close()
            img_curr.close()
            attempt += 1

        print(f"  [QA Loop Warning] SKU {sku} Slot {slot} reached max retries. Saving current best candidate.")
        # Fallback: run one last time with final overrides
        tol = slot_override.get("tolerance", 15.0)
        blend = slot_override.get("blend_range", 80.0)
        img_curr = img_cleaned_func(tol, blend)
        adj_x = slot_override.get("adjust_x", 0)
        adj_y = slot_override.get("adjust_y", 0)
        scale_override = slot_override.get("scale_factor_override", None)

        canvas_final, scale_final, _, _ = engine.compose_studio_image(
            img=img_curr,
            bbox_clean=bbox_clean,
            category=category,
            sku=sku,
            slot=slot,
            is_zoom_view=is_zoom_view,
            bg_color=bg_color,
            target_w=target_w,
            target_h=target_h,
            floor_pct=floor_pct,
            is_centered=is_centered,
            sku_scale=scale_override or sku_scale,
            adjust_x=adj_x,
            adjust_y=adj_y
        )
        img_curr.close()
        return canvas_final, scale_final, False

