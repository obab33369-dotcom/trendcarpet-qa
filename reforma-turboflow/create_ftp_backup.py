import os
import sys
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
BACKUP_ROOT = os.path.join(ONEDRIVE_DIR, "turboflow_backup")

def download_file(url, dest_path):
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, 'wb') as f:
            f.write(data)
        return True, None
    except Exception as e:
        return False, str(e)

def backup_folder(staging_name, staging_path):
    print(f"\n[BACKUP] Processing backup for folder: '{staging_name}'...")
    artiklar_dir = os.path.join(staging_path, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    if not os.path.exists(artiklar_dir):
        print(f"  Staging folder not found: {artiklar_dir}")
        return
        
    backup_artiklar = os.path.join(BACKUP_ROOT, staging_name, "artiklar")
    backup_liten = os.path.join(backup_artiklar, "liten")
    backup_zoom = os.path.join(backup_artiklar, "zoom")
    
    # Collect all SKUs from staging artiklar (files directly in artiklar/)
    staged_files = [f for f in os.listdir(artiklar_dir) if os.path.isfile(os.path.join(artiklar_dir, f))]
    skus = []
    for f in staged_files:
        sku, ext = os.path.splitext(f)
        if ext.lower() in ('.jpg', '.jpeg', '.png'):
            skus.append((sku, ext))
            
    print(f"  Found {len(skus)} SKUs in staging folder.")
    
    download_tasks = []
    
    for sku, ext in skus:
        # 1. Main image: /artiklar/[SKU].jpg
        normal_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}{ext}"
        dest_normal = os.path.join(backup_artiklar, f"{sku}{ext}")
        download_tasks.append((normal_url, dest_normal, f"{sku} (Normal)"))
        
        # Try jpeg/png fallbacks if different from ext
        for fallback_ext in ('.jpg', '.jpeg', '.png'):
            if fallback_ext != ext:
                fallback_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}{fallback_ext}"
                dest_fallback = os.path.join(backup_artiklar, f"{sku}{fallback_ext}")
                download_tasks.append((fallback_url, dest_fallback, f"{sku} (Normal {fallback_ext})"))

        # 2. Liten image: /artiklar/liten/[SKU]_S.jpg
        liten_url = f"https://www.reformasthlm.se/bilder/artiklar/liten/{sku}_S{ext}"
        dest_liten = os.path.join(backup_liten, f"{sku}_S{ext}")
        download_tasks.append((liten_url, dest_liten, f"{sku} (Liten)"))
        
        # 3. Zoom images (we check what zoom files exist in staging zoom/ for this SKU, and fetch them)
        # Check files matching [SKU]_[1-9].jpg in zoom/
        staged_zoom_files = []
        if os.path.exists(zoom_dir):
            pattern = re.compile(rf"^{re.escape(sku)}_\d+\.[a-zA-Z]+$")
            staged_zoom_files = [f for f in os.listdir(zoom_dir) if pattern.match(f)]
            
        for z_file in staged_zoom_files:
            z_sku_slot, z_ext = os.path.splitext(z_file)
            zoom_url = f"https://www.reformasthlm.se/bilder/artiklar/zoom/{z_sku_slot}{z_ext}"
            dest_zoom = os.path.join(backup_zoom, f"{z_sku_slot}{z_ext}")
            download_tasks.append((zoom_url, dest_zoom, f"{z_sku_slot} (Zoom)"))
            
    print(f"  Scheduled {len(download_tasks)} potential file downloads from website...")
    
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
                
            if (idx + 1) % 200 == 0 or (idx + 1) == len(futures):
                print(f"    Progress: {idx + 1}/{len(futures)} tasks completed ({success_count} success, {fail_count} skipped/failed)")
                
    print(f"  Backup for '{staging_name}' completed. Success: {success_count} files downloaded.")

def main():
    print("==================================================")
    print("      CREATING RESTORATION FTP BACKUP FOLDER      ")
    print("==================================================")
    
    # 1. Backup chairs_cropped3
    chairs_path = os.path.join(ONEDRIVE_DIR, "turboflow", "chairs_cropped3")
    backup_folder("chairs_cropped3", chairs_path)
    
    # 2. Backup ftp_upload_cropped
    ftp_path = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped")
    backup_folder("ftp_upload_cropped", ftp_path)
    
    # 3. Backup temporary-ftp-upload
    topaz_path = os.path.join(ONEDRIVE_DIR, "turboflow", "temporary-ftp-upload")
    backup_folder("temporary-ftp-upload", topaz_path)
    
    print("\n==================================================")
    print("             BACKUP PROCESS COMPLETE!             ")
    print("==================================================")
    print(f"📂 Backup root directory: {BACKUP_ROOT}")

if __name__ == "__main__":
    main()
