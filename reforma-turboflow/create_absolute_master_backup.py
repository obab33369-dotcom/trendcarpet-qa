import os
import sys
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BRAND_DICT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\brand_sku_dict.json"
ONEDRIVE_BACKUP_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_backup"

def download_file(url, dest_path):
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
        with open(dest_path, 'wb') as f:
            f.write(data)
        return True, None
    except Exception as e:
        return False, str(e)

def backup_product_images(sku, ext, artiklar_dir, liten_dir, zoom_dir):
    """
    Downloads all active images for a single SKU.
    First downloads the normal image and thumbnail, then sequentially downloads
    zoom images _1, _2... up to _10. Stops as soon as a zoom image is not found (404).
    """
    downloaded = 0
    errors = []
    
    # 1. Download Normal image: /artiklar/[SKU].jpg
    normal_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}{ext}"
    dest_normal = os.path.join(artiklar_dir, f"{sku}{ext}")
    success, err = download_file(normal_url, dest_normal)
    if success:
        downloaded += 1
    
    # 2. Download Liten image: /artiklar/liten/[SKU]_S.jpg
    liten_url = f"https://www.reformasthlm.se/bilder/artiklar/liten/{sku}_S{ext}"
    dest_liten = os.path.join(liten_dir, f"{sku}_S{ext}")
    success, err = download_file(liten_url, dest_liten)
    if success:
        downloaded += 1
        
    # 3. Sequentially download Zoom images: _1, _2... up to _10
    for i in range(1, 11):
        zoom_url = f"https://www.reformasthlm.se/bilder/artiklar/zoom/{sku}_{i}{ext}"
        dest_zoom = os.path.join(zoom_dir, f"{sku}_{i}{ext}")
        
        # Test download
        success, err = download_file(zoom_url, dest_zoom)
        if success:
            downloaded += 1
        else:
            # If we hit an error (like 404), it means no more zoom images exist for this product
            if "404" in str(err) or "not found" in str(err).lower():
                break
            else:
                errors.append(f"Zoom_{i} error: {err}")
                break
                
    return sku, downloaded, errors

def main():
    print("==================================================")
    print("     CREATING ABSOLUTE EXHAUSTIVE CATALOG BACKUP   ")
    print("==================================================")
    
    if not os.path.exists(BRAND_DICT_PATH):
        print(f"❌ Error: Brand dictionary not found at {BRAND_DICT_PATH}!")
        return
        
    with open(BRAND_DICT_PATH, "r", encoding="utf-8") as f:
        brand_sku_dict = json.load(f)
        
    print(f"Loaded {len(brand_sku_dict)} products from the catalog.")
    print(f"Targeting OneDrive Folder: {ONEDRIVE_BACKUP_DIR}")
    
    # Establish FTP directories
    artiklar_dir = os.path.join(ONEDRIVE_BACKUP_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    os.makedirs(artiklar_dir, exist_ok=True)
    os.makedirs(liten_dir, exist_ok=True)
    os.makedirs(zoom_dir, exist_ok=True)
    
    # Prepare task params
    tasks = []
    for slug, info in brand_sku_dict.items():
        sku = info["sku"]
        rel_img_path = info["image_path"]
        _, ext = os.path.splitext(rel_img_path.split('?')[0])
        if not ext:
            ext = '.jpg'
        tasks.append((sku, ext))
        
    print(f"\nScanning and downloading all Zoom (1-10), Liten, and Normal images concurrently...")
    
    total_downloaded = 0
    completed_products = 0
    
    # Use 30 parallel workers for high speed scanning and downloading
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {
            executor.submit(backup_product_images, task[0], task[1], artiklar_dir, liten_dir, zoom_dir): task for task in tasks
        }
        
        for future in as_completed(futures):
            sku, downloaded, errors = future.result()
            completed_products += 1
            total_downloaded += downloaded
            
            if errors:
                print(f"  ⚠️ Warning for SKU {sku}: {errors}")
                
            if completed_products % 50 == 0 or completed_products == len(futures):
                print(f"  Progress: {completed_products}/{len(futures)} products fully scanned ({total_downloaded} total files downloaded)")
                
    print("\n==================================================")
    print("       ABSOLUTE EXHAUSTIVE BACKUP COMPLETE!       ")
    print("==================================================")
    print(f"📂 Master Backup saved to: {ONEDRIVE_BACKUP_DIR}")
    print(f"  └─ /artiklar/      (Normal): {len(os.listdir(artiklar_dir)) - 1} files")
    print(f"  └─ /artiklar/liten/ (Liten):  {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (Zoom):   {len(os.listdir(zoom_dir))} files")
    print(f"✓ Total unique files successfully downloaded: {total_downloaded}")
    print("==================================================")

if __name__ == "__main__":
    main()
