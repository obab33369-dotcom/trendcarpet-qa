import os
import sys
import json
import shutil
import subprocess

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

test_skus = [
    "67099",
    "67100",
    "1400034",
    "H000017689",
    "2300103"
]

project_dir = os.path.dirname(os.path.abspath(__file__))
cache_path = os.path.join(project_dir, "scratch", "classification_cache.json")
bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

print("==================================================")
print("1. CLEANING CACHE FOR TARGET SKUS")
print("==================================================")

def clear_cache_for_skus(file_path, skus):
    if not os.path.exists(file_path):
        print(f"Cache file {file_path} not found. Skipping.")
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        initial_len = len(data)
        keys_to_delete = []
        for key in data.keys():
            for sku in skus:
                if sku.lower() in key.lower():
                    keys_to_delete.append(key)
                    break
        
        for key in keys_to_delete:
            del data[key]
            
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Cleaned {len(keys_to_delete)} entries from {os.path.basename(file_path)}. (Size reduced from {initial_len} to {len(data)})")
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")

clear_cache_for_skus(cache_path, test_skus)
clear_cache_for_skus(bbox_path, test_skus)

print("\n==================================================")
print("2. RUNNING PIPELINE FOR TARGET SKUS (SOURCING FROM TOPAZ/FALLBACK)")
print("==================================================")

env = os.environ.copy()
env["PYTHONPATH"] = project_dir + os.pathsep + env.get("PYTHONPATH", "")
# Force original shadows (Route 2 white background styling)
env["FORCE_ORIGINAL"] = "1"
# IGNORE the white background fix folder to source strictly from Topaz or Fallback
env["IGNORE_FIX_FOLDER"] = "1"

for idx, sku in enumerate(test_skus):
    print(f"\n[{idx+1}/{len(test_skus)}] Starting pipeline run for SKU: {sku}...")
    cmd = [sys.executable, "reforma_pipeline/orchestrator.py", f"--sku={sku}"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            cwd=project_dir,
            env=env
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print("  " + output.strip())
                
        rc = process.poll()
        if rc == 0:
            print(f"✓ SKU {sku} processed successfully.")
        else:
            print(f"❌ SKU {sku} failed with exit code: {rc}")
            
    except Exception as e:
        print(f"❌ Error executing pipeline for SKU {sku}: {e}")

print("\n==================================================")
print("3. COPYING OUTPUTS TO ONEDRIVE tpom FOLDER")
print("==================================================")

onedrive_base = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
source_artiklar = os.path.join(onedrive_base, "turboflow", "ftp_upload_cropped_full", "artiklar")
dest_artiklar = os.path.join(onedrive_base, "turboflow", "tpom", "artiklar")

print(f"Source: {source_artiklar}")
print(f"Destination: {dest_artiklar}")

if not os.path.exists(source_artiklar):
    print(f"[ERROR] Source path {source_artiklar} does not exist. Cannot copy.")
else:
    # Clear existing tpom directory files to prevent mixing old files
    if os.path.exists(dest_artiklar):
        for f in os.listdir(dest_artiklar):
            file_p = os.path.join(dest_artiklar, f)
            if os.path.isfile(file_p):
                try: os.remove(file_p)
                except Exception: pass
        
        liten_p = os.path.join(dest_artiklar, "liten")
        if os.path.exists(liten_p):
            for f in os.listdir(liten_p):
                file_p = os.path.join(liten_p, f)
                if os.path.isfile(file_p):
                    try: os.remove(file_p)
                    except Exception: pass
                    
        zoom_p = os.path.join(dest_artiklar, "zoom")
        if os.path.exists(zoom_p):
            for f in os.listdir(zoom_p):
                file_p = os.path.join(zoom_p, f)
                if os.path.isfile(file_p):
                    try: os.remove(file_p)
                    except Exception: pass

    os.makedirs(dest_artiklar, exist_ok=True)
    os.makedirs(os.path.join(dest_artiklar, "liten"), exist_ok=True)
    os.makedirs(os.path.join(dest_artiklar, "zoom"), exist_ok=True)
    
    copied_count = 0
    for sku in test_skus:
        # Copy main images (in artiklar)
        for f in os.listdir(source_artiklar):
            if f.lower().startswith(sku.lower()) and os.path.isfile(os.path.join(source_artiklar, f)):
                src_file = os.path.join(source_artiklar, f)
                dst_file = os.path.join(dest_artiklar, f)
                shutil.copy2(src_file, dst_file)
                copied_count += 1
                print(f"  Copied: {f} -> tpom/artiklar/")
                
        # Copy small images (in liten)
        src_liten = os.path.join(source_artiklar, "liten")
        dst_liten = os.path.join(dest_artiklar, "liten")
        if os.path.exists(src_liten):
            for f in os.listdir(src_liten):
                if f.lower().startswith(sku.lower()) and os.path.isfile(os.path.join(src_liten, f)):
                    src_file = os.path.join(src_liten, f)
                    dst_file = os.path.join(dst_liten, f)
                    shutil.copy2(src_file, dst_file)
                    copied_count += 1
                    print(f"  Copied: liten/{f} -> tpom/artiklar/liten/")
                    
        # Copy zoom/details (in zoom)
        src_zoom = os.path.join(source_artiklar, "zoom")
        dst_zoom = os.path.join(dest_artiklar, "zoom")
        if os.path.exists(src_zoom):
            for f in os.listdir(src_zoom):
                if f.lower().startswith(sku.lower()) and os.path.isfile(os.path.join(src_zoom, f)):
                    src_file = os.path.join(src_zoom, f)
                    dst_file = os.path.join(dst_zoom, f)
                    shutil.copy2(src_file, dst_file)
                    copied_count += 1
                    print(f"  Copied: zoom/{f} -> tpom/artiklar/zoom/")

    print(f"\nSuccessfully copied {copied_count} files to tpom folder.")

print("\n==================================================")
print("              TPOM TEST PIPELINE RUN COMPLETE     ")
print("==================================================")
