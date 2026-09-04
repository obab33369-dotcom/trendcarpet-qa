import os
import re
import datetime
import json
import shutil

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering", "Baddsoffa Texas Ljusgra (MLM-502580-lightgrey)")

def load_db(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mapping = {}
    for item in data:
        prompt = item.get('prompt', '')
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            idx = int(m.group(1))
            mapping[idx] = {
                "prompt": prompt,
                "refs": [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
            }
    return mapping

batch1 = load_db("rooms_turboflow_batch1.json")
batch2 = load_db("rooms_turboflow_batch2.json")
full_catalog = load_db("rooms_turboflow_full_catalog.json")

def safe_clear_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        return
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            print(f"Could not remove {item}: {e}")

def build_texas_folder():
    print("Cleaning target folder...")
    os.makedirs(TARGET_DIR, exist_ok=True)
    os.makedirs(os.path.join(TARGET_DIR, "reserv"), exist_ok=True)
    
    # Clear main target dir (except reserv folder)
    for item in os.listdir(TARGET_DIR):
        if item == "reserv":
            continue
        item_path = os.path.join(TARGET_DIR, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            print(f"Could not remove {item} in main: {e}")
            
    # Clear reserv folder
    safe_clear_dir(os.path.join(TARGET_DIR, "reserv"))

    dirs_to_scan = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    files_info = []
    for d in dirs_to_scan:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            path = os.path.join(d, f)
            try:
                stat = os.stat(path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files_info.append({
                    "filename": f,
                    "mtime": mtime,
                    "path": path,
                    "dir": os.path.basename(d)
                })
            except Exception:
                pass

    if not files_info:
        print("No files found to process.")
        return

    # Sort files chronologically
    files_info.sort(key=lambda x: x["mtime"])
    
    # Group into clusters
    clusters = []
    current_cluster = [files_info[0]]
    for item in files_info[1:]:
        time_diff = (item["mtime"] - current_cluster[-1]["mtime"]).total_seconds() / 3600.0
        if time_diff > 2.0:
            clusters.append(current_cluster)
            current_cluster = [item]
        else:
            current_cluster.append(item)
    clusters.append(current_cluster)
    
    cluster_db_map = {
        0: ("Batch 2", batch2),
        1: ("Batch 1", batch1),
        2: ("Batch 1", batch1),
        3: ("Full Catalog", full_catalog),
        4: ("Full Catalog", full_catalog)
    }

    copied_main = 0
    copied_reserv = 0

    print("Copying Texas Sofa files...")
    for c_idx, cluster in enumerate(clusters):
        if c_idx not in (0, 1, 2):
            continue
            
        db_label, db = cluster_db_map[c_idx]
        
        for item in cluster:
            fn = item["filename"]
            m = re.match(r"^(\d+)", fn)
            if not m:
                continue
            prefix = int(m.group(1))
            
            if prefix in db:
                refs = db[prefix]["refs"]
                # Find if refs contain Texas/Lucca
                texas_ref_idx = -1
                for idx, r in enumerate(refs):
                    r_lower = r.lower()
                    if "0108" in r_lower or "1397" in r_lower or "texas" in r_lower or "lucca" in r_lower:
                        texas_ref_idx = idx
                        break
                
                if texas_ref_idx != -1:
                    src_path = item["path"]
                    try:
                        if texas_ref_idx == 0:
                            # Primary: copy to main folder
                            dest_path = os.path.join(TARGET_DIR, fn)
                            shutil.copy2(src_path, dest_path)
                            copied_main += 1
                            print(f"Copied to Main: {fn} (from {db_label} index {prefix})")
                        else:
                            # Secondary: copy to reserv folder
                            dest_path = os.path.join(TARGET_DIR, "reserv", fn)
                            shutil.copy2(src_path, dest_path)
                            copied_reserv += 1
                            print(f"Copied to reserv: {fn} (from {db_label} index {prefix})")
                    except Exception as e:
                        print(f"Error copying {fn}: {e}")

    # Copy reference photo
    ref_src = os.path.join(WORKSPACE_DIR, "reforma-original-images", "MLM-502580-lightgrey.jpg")
    if os.path.exists(ref_src):
        ref_dest = os.path.join(TARGET_DIR, "00_REFERENCE_MLM-502580-lightgrey.jpg")
        shutil.copy2(ref_src, ref_dest)
        print("Copied reference image successfully.")
    else:
        print("Warning: Reference image not found at source.")

    print("\n================ COMPLETED REBUILD ================")
    print(f"Main folder: {copied_main} images")
    print(f"Reserv folder: {copied_reserv} images")
    print(f"Total: {copied_main + copied_reserv} images")

if __name__ == "__main__":
    build_texas_folder()
