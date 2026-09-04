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

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
READY_JSON_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready_batch1.json"

ONEDRIVE_BASE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
TEST_TOPAZ_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"

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
    print("      PARTITIONING BATCH 1 INTO 8 SUB-BATCHES      ")
    print("==================================================")
    
    # 1. Load active keys
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at {DB_PATH}.")
        sys.exit(1)
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    active_keys = sorted([k for k in db.keys() if not should_skip_item(k)])
    print(f"Total active items: {len(active_keys)}")
    
    # Separate into furniture and rugs to distribute them evenly as seeds
    furniture_keys = [k for k in active_keys if 'matta' not in k.lower()]
    rug_keys = [k for k in active_keys if 'matta' in k.lower()]
    print(f"  Furniture items as potential seeds: {len(furniture_keys)}")
    print(f"  Rug items as potential seeds: {len(rug_keys)}")
    
    # 2. Split active keys into 8 parts evenly
    # 186 furniture items split into 8:
    # 186 / 8 = 23.25. 23 * 6 = 138, 24 * 2 = 48. Total = 186.
    # 116 rug items split into 8:
    # 116 / 8 = 14.5. 14 * 4 = 56, 15 * 4 = 60. Total = 116.
    part_keys = []
    
    f_idx = 0
    r_idx = 0
    
    for i in range(8):
        # Furniture slice
        f_size = 23 if i < 6 else 24
        f_start = f_idx
        f_end = f_idx + f_size
        f_idx = f_end
        
        # Rug slice
        r_size = 14 if i < 4 else 15
        r_start = r_idx
        r_end = r_idx + r_size
        r_idx = r_end
        
        part_keys.append(sorted(furniture_keys[f_start:f_end] + rug_keys[r_start:r_end]))
    
    for i, keys in enumerate(part_keys):
        f_count = len([k for k in keys if 'matta' not in k.lower()])
        r_count = len([k for k in keys if 'matta' in k.lower()])
        print(f"  Sub-Batch {i+1} (Del {i+1}) active seed items: {len(keys)} (Furniture: {f_count}, Rugs: {r_count})")
        
    part_keys_sets = [set(keys) for keys in part_keys]
    
    # 3. Re-create the seed list to map prompt rows back to their seeds
    seeds = sorted(list(active_keys)) * 4
    
    # 4. Load the generated prompts
    if not os.path.exists(READY_JSON_PATH):
        print(f"[ERROR] Prompt JSON file not found at {READY_JSON_PATH}.")
        sys.exit(1)
        
    with open(READY_JSON_PATH, "r", encoding="utf-8") as f:
        all_rows = json.load(f)
        
    print(f"Total prompt rows loaded: {len(all_rows)}")
    
    part_rows = [[] for _ in range(8)]
    
    # Partition the rows
    for idx, row in enumerate(all_rows):
        pkg_idx = idx // 2
        seed_filename = seeds[pkg_idx]
        
        row_copy = row.copy()
        
        # Determine which part this seed belongs to
        found_part = False
        for part_num in range(8):
            if seed_filename in part_keys_sets[part_num]:
                part_rows[part_num].append(row_copy)
                found_part = True
                break
        
        if not found_part:
            print(f"[WARNING] Seed filename {seed_filename} could not be matched to any part!")
            
    for i, rows in enumerate(part_rows):
        print(f"  Sub-Batch {i+1} (Del {i+1}) prompt rows: {len(rows)}")
        
    # 5. Write Sub-Batch prompt files (both in Local Workspace and OneDrive)
    workspace_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"
    onedrive_dir = ONEDRIVE_BASE_DIR
    
    for part_num in range(8):
        p_idx = part_num + 1
        
        # Local paths
        json_path_local = os.path.join(workspace_dir, f"turboflow_ready_batch1_del{p_idx}.json")
        csv_path_local = os.path.join(workspace_dir, f"turboflow_ready_batch1_del{p_idx}.csv")
        txt_path_local = os.path.join(workspace_dir, f"prompts_only_batch1_del{p_idx}.txt")
        
        # OneDrive paths
        json_path_od = os.path.join(onedrive_dir, f"turboflow_ready_batch1_del{p_idx}.json")
        csv_path_od = os.path.join(onedrive_dir, f"turboflow_ready_batch1_del{p_idx}.csv")
        txt_path_od = os.path.join(onedrive_dir, f"turboflow_ready_batch1_del{p_idx}.txt") # Raw txt format
        
        rows = part_rows[part_num]
        
        # Write JSON files
        for path in (json_path_local, json_path_od):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
                
        # Write CSV files
        for path in (csv_path_local, csv_path_od):
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(["prompt", "image_references", "image_tags", "aspect_ratio"])
                for r in rows:
                    writer.writerow([r["prompt"], r["image_references"], r["image_tags"], r["aspect_ratio"]])
                    
        # Write Raw TXT files
        for path in (txt_path_local, txt_path_od):
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                for r in rows:
                    f.write(r["prompt"] + "\n")
                    
        print(f"-> Del {p_idx} prompt files written successfully.")
        
    # 6. Copy active images to separate OneDrive folders (Basic Copy, will be optimized by optimize_folders.py)
    print("\n[INFO] Copying active product images into structured sub-batches...")
    for part_num in range(8):
        p_idx = part_num + 1
        onedrive_dest = os.path.join(onedrive_dir, f"turboflow_batch1_produkter_aktiva_del{p_idx}")
        
        print(f"-> Preparing folder for Part {p_idx} -> {onedrive_dest}")
        os.makedirs(onedrive_dest, exist_ok=True)
        
        # Clean folder first
        for filename in os.listdir(onedrive_dest):
            try:
                os.unlink(os.path.join(onedrive_dest, filename))
            except Exception:
                pass
                
        copied_count = 0
        missing_count = 0
        
        # Copy only the active seed items for this part as starting files
        for filename in part_keys[part_num]:
            src_path = os.path.join(TEST_TOPAZ_DIR, filename)
            if os.path.exists(src_path):
                dest_path = os.path.join(onedrive_dest, filename)
                shutil.copy2(src_path, dest_path)
                copied_count += 1
            else:
                missing_count += 1
                
        print(f"   -> Copied {copied_count} base files to Del {p_idx} folder. (Missing: {missing_count})")
        
    print("\n==================================================")
    print("         PARTITIONING SUCCESS!                    ")
    print("==================================================")
    print(f"👉 Outputs successfully staged in OneDrive at:")
    print(f"   C:\\Users\\AndronikLindgren\\OneDrive - CaMa Gruppen AB\\Pictures")
    print("==================================================")

if __name__ == "__main__":
    main()
