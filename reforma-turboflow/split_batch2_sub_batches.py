import os
import shutil
import sys
import json
import csv

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"
READY_JSON_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready_batch2.json"
ONEDRIVE_BASE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

def clean_str(s: str) -> str:
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
    for c, r in repl.items():
        s = s.replace(c, r)
    return s.lower()

def should_skip_item(filename: str) -> bool:
    fname = filename.lower()
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    cleaned_fname = clean_str(fname)
    for kw in skip_keywords:
        if kw in fname or clean_str(kw) in cleaned_fname:
            return True
    return False

def main():
    print("==================================================")
    print("      PARTITIONING BATCH 2 INTO SUB-BATCHES      ")
    print("==================================================")
    
    # 1. Load active keys
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    active_keys = sorted([k for k in db.keys() if not should_skip_item(k)])
    print(f"Total active items: {len(active_keys)}")
    
    # 2. Split active keys into 2 parts
    part1_keys = sorted(active_keys[:87])  # 87 items
    part2_keys = sorted(active_keys[87:])  # 86 items
    print(f"Sub-Batch 1 (Del 1) active items: {len(part1_keys)}")
    print(f"Sub-Batch 2 (Del 2) active items: {len(part2_keys)}")
    
    # Create sets for O(1) lookups
    part1_keys_set = set(part1_keys)
    part2_keys_set = set(part2_keys)
    
    # 3. Re-create the seed list to map prompt rows back to their seeds
    seeds = active_keys * 2
    
    # 4. Load the generated 692 prompts
    with open(READY_JSON_PATH, "r", encoding="utf-8") as f:
        all_rows = json.load(f)
        
    print(f"Total prompt rows loaded: {len(all_rows)}")
    
    part1_rows = []
    part2_rows = []
    
    # Partition the rows
    for i, row in enumerate(all_rows):
        pkg_idx = i // 2
        seed_filename = seeds[pkg_idx]
        
        # Add the seed context information to the row for tracking
        row_copy = row.copy()
        
        if seed_filename in part1_keys_set:
            part1_rows.append(row_copy)
        elif seed_filename in part2_keys_set:
            part2_rows.append(row_copy)
            
    print(f"Sub-Batch 1 (Del 1) prompt rows: {len(part1_rows)}")
    print(f"Sub-Batch 2 (Del 2) prompt rows: {len(part2_rows)}")
    
    # 5. Write Sub-Batch prompt files
    base_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"
    
    # Write JSONs
    json_path_del1 = os.path.join(base_dir, "turboflow_ready_batch2_del1.json")
    json_path_del2 = os.path.join(base_dir, "turboflow_ready_batch2_del2.json")
    with open(json_path_del1, "w", encoding="utf-8") as f:
        json.dump(part1_rows, f, ensure_ascii=False, indent=2)
    with open(json_path_del2, "w", encoding="utf-8") as f:
        json.dump(part2_rows, f, ensure_ascii=False, indent=2)
        
    # Write TXT prompts-only
    txt_path_del1 = os.path.join(base_dir, "prompts_only_batch2_del1.txt")
    txt_path_del2 = os.path.join(base_dir, "prompts_only_batch2_del2.txt")
    with open(txt_path_del1, "w", encoding="utf-8", newline="\n") as f:
        for r in part1_rows:
            f.write(r["prompt"] + "\n")
    with open(txt_path_del2, "w", encoding="utf-8", newline="\n") as f:
        for r in part2_rows:
            f.write(r["prompt"] + "\n")
            
    # Write CSVs
    csv_path_del1 = os.path.join(base_dir, "turboflow_ready_batch2_del1.csv")
    csv_path_del2 = os.path.join(base_dir, "turboflow_ready_batch2_del2.csv")
    
    for path, rows in [(csv_path_del1, part1_rows), (csv_path_del2, part2_rows)]:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["prompt", "image_references", "image_tags", "aspect_ratio"])
            for r in rows:
                writer.writerow([r["prompt"], r["image_references"], r["image_tags"], r["aspect_ratio"]])

    print("\n✓ Prompt files successfully partitioned!")
    
    # 6. Copy OneDrive image directories
    onedrive_src = os.path.join(ONEDRIVE_BASE_DIR, "turboflow_batch2_produkter")
    onedrive_dest_del1 = os.path.join(ONEDRIVE_BASE_DIR, "turboflow_batch2_produkter_aktiva_del1")
    onedrive_dest_del2 = os.path.join(ONEDRIVE_BASE_DIR, "turboflow_batch2_produkter_aktiva_del2")
    
    # Del 1 Clean and Copy
    print(f"\n📂 Partitioning image folder Part 1 -> {onedrive_dest_del1}")
    os.makedirs(onedrive_dest_del1, exist_ok=True)
    for filename in os.listdir(onedrive_dest_del1):
        try: os.unlink(os.path.join(onedrive_dest_del1, filename))
        except Exception: pass
        
    copied_del1 = 0
    for filename in part1_keys:
        src = os.path.join(onedrive_src, filename)
        dest = os.path.join(onedrive_dest_del1, filename)
        if os.path.exists(src):
            shutil.copy2(src, dest)
            copied_del1 += 1
    print(f"   ✓ Copied {copied_del1} active files to Del 1 folder.")
    
    # Del 2 Clean and Copy
    print(f"📂 Partitioning image folder Part 2 -> {onedrive_dest_del2}")
    os.makedirs(onedrive_dest_del2, exist_ok=True)
    for filename in os.listdir(onedrive_dest_del2):
        try: os.unlink(os.path.join(onedrive_dest_del2, filename))
        except Exception: pass
        
    copied_del2 = 0
    for filename in part2_keys:
        src = os.path.join(onedrive_src, filename)
        dest = os.path.join(onedrive_dest_del2, filename)
        if os.path.exists(src):
            shutil.copy2(src, dest)
            copied_del2 += 1
    print(f"   ✓ Copied {copied_del2} active files to Del 2 folder.")
    
    print("\n==================================================")
    print("         PARTITIONING SUCCESS!                    ")
    print("==================================================")
    print(f"👉 Sub-Batch 1 Prompts: {txt_path_del1} ({len(part1_rows)} lines)")
    print(f"👉 Sub-Batch 1 Renders: {onedrive_dest_del1} ({copied_del1} files)")
    print(f"👉 Sub-Batch 2 Prompts: {txt_path_del2} ({len(part2_rows)} lines)")
    print(f"👉 Sub-Batch 2 Renders: {onedrive_dest_del2} ({copied_del2} files)")
    print("==================================================")

if __name__ == "__main__":
    main()
