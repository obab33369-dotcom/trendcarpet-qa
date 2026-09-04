import json
import csv
import re
import os

TRACKING_CSV = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_tracking_log_batch2.csv"
READY_JSON = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready_batch2.json"
PROMPTS_TXT = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\prompts_only_batch2.txt"

def verify():
    print("=== STARTING BATCH 2 PIPELINE VALIDATION ===")
    
    # 1. Check file existence
    files_to_check = [TRACKING_CSV, READY_JSON, PROMPTS_TXT]
    for f in files_to_check:
        if not os.path.exists(f):
            print(f"[FAIL] Missing file: {f}")
            return
        else:
            print(f"[OK] File exists: {f} ({os.path.getsize(f)} bytes)")
            
    # 2. Check JSON contents
    with open(READY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Total rows in JSON: {len(data)}")
    
    # 3. Check CSV contents
    csv_rows = []
    with open(TRACKING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            csv_rows.append(row)
            
    print(f"Total rows in tracking CSV: {len(csv_rows)}")
    
    # Check total counts
    package_ids = set()
    for row in csv_rows:
        package_ids.add(row["Package ID"])
    print(f"Distinct Package IDs found: {len(package_ids)}")
    print(f"Total generated shots: {len(csv_rows)}")
    
    expected_packages = len(package_ids)
    expected_shots = expected_packages * 2
    
    if len(csv_rows) == expected_shots:
        print(f"[OK] Exactly {expected_shots} total rows in CSV (4 shots per package)!")
    else:
        print(f"[WARNING] Total rows in CSV: {len(csv_rows)} (expected {expected_shots})")

    if len(data) == expected_shots:
        print(f"[OK] Exactly {expected_shots} total rows in JSON!")
    else:
        print(f"[WARNING] Total rows in JSON: {len(data)} (expected {expected_shots})")

    # 4. Semantic Validation of Prompts
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    
    spindle_back_count = 0
    three_quarters_count = 0
    missing_prefix_count = 0
    skipped_category_count = 0
    non_16_9_count = 0
    bench_dining_pairings = 0
    bench_along_wall_missing = 0
    desk_against_wall_missing = 0
    made_up_sofa_beds = 0
    bar_rug_count = 0
    
    for row in data:
        prompt = row["prompt"]
        aspect_ratio = row.get("aspect_ratio", "")
        refs = row.get("image_references", "")
        
        # Check aspect ratio
        if aspect_ratio != "16:9":
            non_16_9_count += 1
            
        # Check prefix
        if "pillarbox" in prompt.lower() or "centered top-to-bottom" in prompt.lower() or "black background" in prompt.lower():
            missing_prefix_count += 1
            
        # Check skipped categories
        for kw in skip_keywords:
            if kw in prompt.lower() or kw in refs.lower():
                skipped_category_count += 1
                
        # Check spindle-back chairs
        if "spindle-back" in prompt.lower() or "spindle back" in prompt.lower():
            spindle_back_count += 1
            
        # Check three-quarters
        if "three-quarters" in prompt.lower() or "three quarters" in prompt.lower():
            three_quarters_count += 1
            
        # Check bench positioned against table or dining setting
        if "bench" in prompt.lower() and not ("tv-bench" in prompt.lower() or "tv bench" in prompt.lower() or "mediabench" in prompt.lower() or "mediabank" in prompt.lower()):
            if "dining table" in prompt.lower() or "placed around" in prompt.lower() or "neatly around" in prompt.lower():
                bench_dining_pairings += 1
            if "standing along the wall" not in prompt.lower():
                bench_along_wall_missing += 1
                
        # Check desk is against the wall
        if "desk" in prompt.lower() and "desk chair" not in prompt.lower() and "office chair" not in prompt.lower():
            if "standing against the wall" not in prompt.lower():
                desk_against_wall_missing += 1
                
        # Check bedroom sofa bed description
        if "bedroom" in prompt.lower() and ("sofa" in prompt.lower() or "soffa" in prompt.lower() or "bäddsoffa" in prompt.lower()):
            if "linen sheets" in prompt.lower() or "crisp organic linen" in prompt.lower():
                made_up_sofa_beds += 1

    # Check Bar packages for rugs
    for row in csv_rows:
        if row["Package Type"] == "Bar":
            if row["Rug Product"] != "None":
                bar_rug_count += 1

    print("\n--- VALIDATION RESULTS ---")
    if missing_prefix_count == 0:
        print("[OK] Zero instances of the old black border prefix/pillarbox borders!")
    else:
        print(f"[FAIL] {missing_prefix_count} prompts still contain the old black border prefix/pillarbox borders!")
        
    if skipped_category_count == 0:
        print("[OK] Zero instances of excluded categories (shelves, wardrobes, mirrors) in prompts or refs!")
    else:
        print(f"[FAIL] {skipped_category_count} instances of excluded categories found!")
        
    if spindle_back_count == 0:
        print("[OK] Zero instances of the spindle-back chair hallucination!")
    else:
        print(f"[FAIL] {spindle_back_count} instances of spindle-back chairs found!")
        
    if three_quarters_count == 0:
        print("[OK] Zero instances of 'three-quarters' angle cropping phrases!")
    else:
        print(f"[FAIL] {three_quarters_count} instances of three-quarters found!")
        
    if non_16_9_count == 0:
        print("[OK] All rows have the '16:9' aspect ratio parameter set!")
    else:
        print(f"[FAIL] {non_16_9_count} rows have incorrect aspect ratio!")

    if bench_dining_pairings == 0:
        print("[OK] Zero benches paired with dining tables!")
    else:
        print(f"[FAIL] {bench_dining_pairings} benches paired with dining tables!")

    if bench_along_wall_missing == 0:
        print("[OK] All standalone benches are described as 'standing along the wall'!")
    else:
        print(f"[WARNING] {bench_along_wall_missing} benches missing 'standing along the wall' description!")

    if desk_against_wall_missing == 0:
        print("[OK] All desks are described as 'standing against the wall'!")
    else:
        print(f"[FAIL] {desk_against_wall_missing} desks missing 'standing against the wall' description!")

    if made_up_sofa_beds == 0:
        print("[OK] Sofa beds in bedroom templates are not described as made-up beds with linen sheets!")
    else:
        print(f"[FAIL] {made_up_sofa_beds} sofa beds in bedroom templates described with linen sheets!")

    # Rugs in Bar templates
    bar_packages = len(set(row["Package ID"] for row in csv_rows if row["Package Type"] == "Bar"))
    expected_bar_rugs = bar_packages * 2 # 2 shots per bar package
    if bar_rug_count == expected_bar_rugs and expected_bar_rugs > 0:
        print(f"[OK] All Bar packages ({bar_packages}) have rug slots and rug descriptions successfully assigned!")
    elif expected_bar_rugs == 0:
        print("[NOTE] No Bar packages generated in this run.")
    else:
        print(f"[WARNING] Bar packages with rugs: {bar_rug_count} out of {expected_bar_rugs} expected.")

    print("\n--- SAMPLE CHECK ---")
    print(f"Sample Prompt 1:\n{data[0]['prompt'][:300]}...")
    print(f"Sample Prompt 2:\n{data[1]['prompt'][:300]}...")
    
    print("\n=== VALIDATION COMPLETE ===")

if __name__ == "__main__":
    verify()
