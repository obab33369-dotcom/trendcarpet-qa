import os
import sys
import json
import shutil

# Ensure standard streams are configured to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def clear_cache_for_skus(file_path, skus):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Skipping.")
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

if __name__ == "__main__":
    # Load target SKUs
    skus_json_path = os.path.join(project_dir, "scratch", "remaining_skus.json")
    if not os.path.exists(skus_json_path):
        print(f"[ERROR] remaining_skus.json not found at {skus_json_path}")
        sys.exit(1)

    with open(skus_json_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    if "--test" in sys.argv:
        candidates = candidates[:2]
        print("[TEST MODE] Limiting run to first 2 SKUs.")

    remaining_skus = [c["sku"] for c in candidates]
    print(f"Loaded {len(remaining_skus)} remaining SKUs to process.")

    # Paths for cache and bbox db
    cache_path = os.path.join(project_dir, "scratch", "classification_cache.json")
    bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

    print("\n==================================================")
    print("1. CLEANING CACHE FOR REMAINING SKUS")
    print("==================================================")
    clear_cache_for_skus(cache_path, remaining_skus)
    clear_cache_for_skus(bbox_path, remaining_skus)

    print("\n==================================================")
    print("2. RUNNING PIPELINE FOR REMAINING SKUS")
    print("==================================================")

    # Set environment variables
    os.environ["FORCE_ORIGINAL"] = "1"
    os.environ["IGNORE_FIX_FOLDER"] = "1"

    # Import run_pipeline here so environment variables are loaded
    from reforma_pipeline.orchestrator import run_pipeline

    try:
        # Run the pipeline for the list of remaining SKUs
        run_pipeline(limit_sku=remaining_skus, dry_run=False)
        print("✓ Pipeline execution finished.")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)

    print("\n==================================================")
    print("3. COPYING OUTPUTS TO FTP artiklar FOLDER")
    print("==================================================")

    onedrive_base = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
    source_artiklar = os.path.join(onedrive_base, "turboflow", "ftp_upload_cropped_full", "artiklar")
    dest_artiklar = os.path.join(onedrive_base, "26-06-18-FTP-Remaining", "artiklar")

    print(f"Source: {source_artiklar}")
    print(f"Destination: {dest_artiklar}")

    if not os.path.exists(source_artiklar):
        print(f"[ERROR] Source path {source_artiklar} does not exist. Cannot copy.")
    else:
        os.makedirs(dest_artiklar, exist_ok=True)
        os.makedirs(os.path.join(dest_artiklar, "liten"), exist_ok=True)
        os.makedirs(os.path.join(dest_artiklar, "zoom"), exist_ok=True)
        
        copied_count = 0
        sku_set_lower = {sku.lower() for sku in remaining_skus}
        
        # Copy main images (in artiklar)
        for f in os.listdir(source_artiklar):
            if os.path.isfile(os.path.join(source_artiklar, f)):
                sku_from_file = os.path.splitext(f)[0].lower()
                if sku_from_file in sku_set_lower:
                    src_file = os.path.join(source_artiklar, f)
                    dst_file = os.path.join(dest_artiklar, f)
                    shutil.copy2(src_file, dst_file)
                    copied_count += 1
                    
        # Copy small images (in liten)
        src_liten = os.path.join(source_artiklar, "liten")
        dst_liten = os.path.join(dest_artiklar, "liten")
        if os.path.exists(src_liten):
            for f in os.listdir(src_liten):
                if os.path.isfile(os.path.join(src_liten, f)):
                    # Filename format: [SKU]_S.jpg
                    sku_from_file = f.rsplit('_', 1)[0].lower()
                    if sku_from_file in sku_set_lower:
                        src_file = os.path.join(src_liten, f)
                        dst_file = os.path.join(dst_liten, f)
                        shutil.copy2(src_file, dst_file)
                        copied_count += 1
                        
        # Copy zoom/details (in zoom)
        src_zoom = os.path.join(source_artiklar, "zoom")
        dst_zoom = os.path.join(dest_artiklar, "zoom")
        if os.path.exists(src_zoom):
            for f in os.listdir(src_zoom):
                if os.path.isfile(os.path.join(src_zoom, f)):
                    # Filename format: [SKU]_[slot].jpg
                    sku_from_file = f.rsplit('_', 1)[0].lower()
                    if sku_from_file in sku_set_lower:
                        src_file = os.path.join(src_zoom, f)
                        dst_file = os.path.join(dst_zoom, f)
                        shutil.copy2(src_file, dst_file)
                        copied_count += 1

        print(f"\nSuccessfully copied {copied_count} files to: {dest_artiklar}")

    print("\n==================================================")
    print("             REMAINING PRODUCTS RUN COMPLETE      ")
    print("==================================================")
