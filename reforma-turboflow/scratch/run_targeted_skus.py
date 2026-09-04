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

# Add project root to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
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

def delete_staging_files(staging_dir, skus):
    if not os.path.exists(staging_dir):
        print(f"Staging dir {staging_dir} not found. Skipping deletion.")
        return
    
    print(f"\nDeleting existing staging files for SKUs: {skus}")
    skus_lower = [sku.lower() for sku in skus]
    
    # 1. Delete main images in artiklar
    deleted_count = 0
    for f in os.listdir(staging_dir):
        p = os.path.join(staging_dir, f)
        if os.path.isfile(p):
            sku_name = os.path.splitext(f)[0].lower()
            if sku_name in skus_lower:
                os.remove(p)
                print(f"Removed: {f}")
                deleted_count += 1
                
    # 2. Delete small images in liten
    liten_dir = os.path.join(staging_dir, "liten")
    if os.path.exists(liten_dir):
        for f in os.listdir(liten_dir):
            p = os.path.join(liten_dir, f)
            if os.path.isfile(p):
                sku_name = f.rsplit('_', 1)[0].lower()
                if sku_name in skus_lower:
                    os.remove(p)
                    print(f"Removed: liten/{f}")
                    deleted_count += 1
                    
    # 3. Delete zoom images in zoom
    zoom_dir = os.path.join(staging_dir, "zoom")
    if os.path.exists(zoom_dir):
        for f in os.listdir(zoom_dir):
            p = os.path.join(zoom_dir, f)
            if os.path.isfile(p):
                sku_name = f.rsplit('_', 1)[0].lower()
                if sku_name in skus_lower:
                    os.remove(p)
                    print(f"Removed: zoom/{f}")
                    deleted_count += 1
                    
    print(f"Total deleted staging files: {deleted_count}")

if __name__ == "__main__":
    target_skus = ["MLM-502850-dark-grey", "MLM-502850", "2507-natur", "2507-walnut", "1310-L-S"]
    print(f"Target SKUs to run: {target_skus}")

    onedrive_base = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
    source_artiklar = os.path.join(onedrive_base, "turboflow", "ftp_upload_cropped_full", "artiklar")

    # Clean staging files first to force re-run
    delete_staging_files(source_artiklar, target_skus)

    # Paths for cache and bbox db
    cache_path = os.path.join(project_dir, "scratch", "classification_cache.json")
    bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

    print("\n==================================================")
    print("1. CLEANING CACHE FOR TARGET SKUS")
    print("==================================================")
    clear_cache_for_skus(cache_path, target_skus)
    clear_cache_for_skus(bbox_path, target_skus)

    print("\n==================================================")
    print("2. RUNNING PIPELINE FOR TARGET SKUS")
    print("==================================================")

    # Set environment variables
    os.environ["FORCE_ORIGINAL"] = "1"
    os.environ["IGNORE_FIX_FOLDER"] = "1"

    # Import run_pipeline here so environment variables are loaded
    from reforma_pipeline.orchestrator import run_pipeline

    try:
        # Run the pipeline for our targeted SKUs
        run_pipeline(limit_sku=target_skus, dry_run=False)
        print("✓ Pipeline execution finished.")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)

    print("\n==================================================")
    print("3. COPYING OUTPUTS TO FTP artiklar FOLDER")
    print("==================================================")

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
        sku_set_lower = {sku.lower() for sku in target_skus}
        
        # Copy main images (in artiklar)
        for f in os.listdir(source_artiklar):
            if os.path.isfile(os.path.join(source_artiklar, f)):
                sku_from_file = os.path.splitext(f)[0].lower()
                if sku_from_file in sku_set_lower:
                    src_file = os.path.join(source_artiklar, f)
                    dst_file = os.path.join(dest_artiklar, f)
                    shutil.copy2(src_file, dst_file)
                    print(f"Copied: {f}")
                    copied_count += 1
                    
        # Copy small images (in liten)
        src_liten = os.path.join(source_artiklar, "liten")
        dst_liten = os.path.join(dest_artiklar, "liten")
        if os.path.exists(src_liten):
            for f in os.listdir(src_liten):
                if os.path.isfile(os.path.join(src_liten, f)):
                    sku_from_file = f.rsplit('_', 1)[0].lower()
                    if sku_from_file in sku_set_lower:
                        src_file = os.path.join(src_liten, f)
                        dst_file = os.path.join(dst_liten, f)
                        shutil.copy2(src_file, dst_file)
                        print(f"Copied: liten/{f}")
                        copied_count += 1
                        
        # Copy zoom/details (in zoom)
        src_zoom = os.path.join(source_artiklar, "zoom")
        dst_zoom = os.path.join(dest_artiklar, "zoom")
        if os.path.exists(src_zoom):
            for f in os.listdir(src_zoom):
                if os.path.isfile(os.path.join(src_zoom, f)):
                    sku_from_file = f.rsplit('_', 1)[0].lower()
                    if sku_from_file in sku_set_lower:
                        src_file = os.path.join(src_zoom, f)
                        dst_file = os.path.join(dst_zoom, f)
                        shutil.copy2(src_file, dst_file)
                        print(f"Copied: zoom/{f}")
                        copied_count += 1

        print(f"\nSuccessfully copied {copied_count} files to: {dest_artiklar}")
        print("\n==================================================")
        print("             TARGETED PRODUCTS RUN COMPLETE       ")
        print("==================================================")
