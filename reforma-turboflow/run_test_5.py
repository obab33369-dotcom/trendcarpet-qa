import os
import sys
import json
import shutil
import subprocess

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

test_skus = [
    "WS-8651A-BlackBlack-NEW",
    "WD2001-KD-white",
    "19791-black-oak",
    "19791-walnut",
    "1091-white-pigmented"
]

project_dir = os.path.dirname(os.path.abspath(__file__))
# Note: caches are in the workspace scratch folder, which is one level up from reforma-turboflow
cache_path = os.path.join(project_dir, "scratch", "classification_cache.json")
bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

print("==================================================")
# 1. Clear caches for target SKUs
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
        # Delete keys that contain any of the target SKUs
        keys_to_delete = []
        for key in data.keys():
            for sku in skus:
                if sku.lower() in key.lower():
                    keys_to_delete.append(key)
                    break
        
        for key in keys_to_delete:
            del data[key]
            
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Cleaned {len(keys_to_delete)} entries from {os.path.basename(file_path)}. (Size reduced from {initial_len} to {len(data)})")
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")

clear_cache_for_skus(cache_path, test_skus)
clear_cache_for_skus(bbox_path, test_skus)

# 2. Run pipeline for each SKU
print("\n==================================================")
print("2. RUNNING PIPELINE FOR TARGET SKUS")
print("==================================================")

env = os.environ.copy()
env["PYTHONPATH"] = project_dir + os.pathsep + env.get("PYTHONPATH", "")
env["FORCE_ORIGINAL"] = "1"

for idx, sku in enumerate(test_skus):
    print(f"\n[{idx+1}/{len(test_skus)}] Starting pipeline run for SKU: {sku}...")
    # Run the orchestrator script
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

# 3. Copy outputs to OneDrive test directory
print("\n==================================================")
print("3. COPYING OUTPUTS TO ONEDRIVE DEDICATED FOLDER")
print("==================================================")

onedrive_base = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
source_artiklar = os.path.join(onedrive_base, "turboflow", "ftp_upload_cropped_full", "artiklar")
dest_artiklar = os.path.join(onedrive_base, "turboflow", "ftp_upload_test_5", "artiklar")

print(f"Source: {source_artiklar}")
print(f"Destination: {dest_artiklar}")

if not os.path.exists(source_artiklar):
    print(f"[ERROR] Source path {source_artiklar} does not exist. Cannot copy.")
else:
    # Do not use rmtree which causes OneDrive locking errors. Just copy/overwrite files directly.
    os.makedirs(dest_artiklar, exist_ok=True)
    os.makedirs(os.path.join(dest_artiklar, "liten"), exist_ok=True)
    os.makedirs(os.path.join(dest_artiklar, "zoom"), exist_ok=True)
    
    copied_count = 0
    # Copy main outputs, liten, and zoom
    # Loop over the SKUs and copy only files starting with them
    for sku in test_skus:
        # Check files in source artiklar
        for f in os.listdir(source_artiklar):
            if f.lower().startswith(sku.lower()):
                src_file = os.path.join(source_artiklar, f)
                dst_file = os.path.join(dest_artiklar, f)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
                    copied_count += 1
                    print(f"  Copied: {f} -> ftp_upload_test_5/artiklar/")
                    
        # Check files in source liten
        src_liten = os.path.join(source_artiklar, "liten")
        dst_liten = os.path.join(dest_artiklar, "liten")
        if os.path.exists(src_liten):
            for f in os.listdir(src_liten):
                if f.lower().startswith(sku.lower()):
                    src_file = os.path.join(src_liten, f)
                    dst_file = os.path.join(dst_liten, f)
                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, dst_file)
                        copied_count += 1
                        print(f"  Copied: liten/{f} -> ftp_upload_test_5/artiklar/liten/")
                        
        # Check files in source zoom
        src_zoom = os.path.join(source_artiklar, "zoom")
        dst_zoom = os.path.join(dest_artiklar, "zoom")
        if os.path.exists(src_zoom):
            for f in os.listdir(src_zoom):
                if f.lower().startswith(sku.lower()):
                    src_file = os.path.join(src_zoom, f)
                    dst_file = os.path.join(dst_zoom, f)
                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, dst_file)
                        copied_count += 1
                        print(f"  Copied: zoom/{f} -> ftp_upload_test_5/artiklar/zoom/")

    print(f"\nSuccessfully copied {copied_count} files to OneDrive dedicated folder.")

print("\n==================================================")
print("              PIPELINE TESTS COMPLETE             ")
print("==================================================")
