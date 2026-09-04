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
        # Check and download
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
        with open(dest_path, 'wb') as f:
            f.write(data)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    print("==================================================")
    print("     CREATING MASTER CATALOG BACKUP ON ONEDRIVE   ")
    print("==================================================")
    
    if not os.path.exists(BRAND_DICT_PATH):
        print(f"❌ Error: Brand dictionary not found at {BRAND_DICT_PATH}!")
        return
        
    with open(BRAND_DICT_PATH, "r", encoding="utf-8") as f:
        brand_sku_dict = json.load(f)
        
    print(f"Loaded {len(brand_sku_dict)} products from the catalog.")
    
    # Establish subdirectories to mirror FTP structure on OneDrive
    artiklar_dir = os.path.join(ONEDRIVE_BACKUP_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    os.makedirs(artiklar_dir, exist_ok=True)
    os.makedirs(liten_dir, exist_ok=True)
    os.makedirs(zoom_dir, exist_ok=True)
    
    download_tasks = []
    
    for slug, info in brand_sku_dict.items():
        sku = info["sku"]
        rel_img_path = info["image_path"]
        
        # Determine the file extension from the scraped image path
        _, ext = os.path.splitext(rel_img_path.split('?')[0])
        if not ext:
            ext = '.jpg'
            
        # Standard Askås paths
        # 1. Normal: /artiklar/[SKU].jpg
        normal_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}{ext}"
        dest_normal = os.path.join(artiklar_dir, f"{sku}{ext}")
        download_tasks.append((normal_url, dest_normal, f"{sku} (Normal)"))
        
        # 2. Liten: /artiklar/liten/[SKU]_S.jpg
        liten_url = f"https://www.reformasthlm.se/bilder/artiklar/liten/{sku}_S{ext}"
        dest_liten = os.path.join(liten_dir, f"{sku}_S{ext}")
        download_tasks.append((liten_url, dest_liten, f"{sku} (Liten)"))
        
        # 3. Zoom 1: /artiklar/zoom/[SKU]_1.jpg
        zoom_url = f"https://www.reformasthlm.se/bilder/artiklar/zoom/{sku}_1{ext}"
        dest_zoom = os.path.join(zoom_dir, f"{sku}_1{ext}")
        download_tasks.append((zoom_url, dest_zoom, f"{sku} (Zoom 1)"))
        
    print(f"\nScheduling {len(download_tasks)} downloads with 20 parallel threads...")
    
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(download_file, task[0], task[1]): task for task in download_tasks
        }
        
        for idx, future in enumerate(as_completed(futures)):
            task = futures[future]
            name = task[2]
            success, err = future.result()
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                # Suppress normal 404/not found errors for small/zoom images if they don't exist
                if "404" not in str(err):
                    print(f"  ⚠️ Warning downloading {name}: {err}")
                    
            if (idx + 1) % 150 == 0 or (idx + 1) == len(futures):
                print(f"  Progress: {idx + 1}/{len(futures)} tasks completed ({success_count} success, {fail_count} skipped/failed)")
                
    print("\n==================================================")
    print("         MASTER ONEDRIVE BACKUP COMPLETED!        ")
    print("==================================================")
    print(f"📂 Master Backup saved to: {ONEDRIVE_BACKUP_DIR}")
    print(f"  └─ /artiklar/      (Normal, 1000px): {len(os.listdir(artiklar_dir)) - 1} files")
    print(f"  └─ /artiklar/liten/ (Liten, 400px):  {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (Zoom, 2000px):  {len(os.listdir(zoom_dir))} files")
    print(f"✓ Total original image files downloaded: {success_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
