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

def build_clean_texas():
    print("Cleaning target folder...")
    safe_clear_dir(TARGET_DIR)
    os.makedirs(os.path.join(TARGET_DIR, "reserv"), exist_ok=True)

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
    
    copied_main = 0
    copied_reserv = 0

    print("Copying EXACT Texas Ljusgra (0108) files from Batch 1...")
    for c_idx, cluster in enumerate(clusters):
        # We only care about Cluster 2 and Cluster 3 (which map to Batch 1)
        if c_idx not in (1, 2):
            continue
            
        for item in cluster:
            fn = item["filename"]
            m = re.match(r"^(\d+)", fn)
            if not m:
                continue
            prefix = int(m.group(1))
            
            if prefix in batch1:
                refs = batch1[prefix]["refs"]
                # Strict check for 0108 (Texas Ljusgra)
                texas_ref_idx = -1
                for idx, r in enumerate(refs):
                    if "0108" in r:
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
                            print(f"Copied to Main: {fn} (index {prefix})")
                        else:
                            # Secondary: copy to reserv folder
                            dest_path = os.path.join(TARGET_DIR, "reserv", fn)
                            shutil.copy2(src_path, dest_path)
                            copied_reserv += 1
                            print(f"Copied to reserv: {fn} (index {prefix})")
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
    build_clean_texas()
