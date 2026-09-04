import os
import sys
import urllib.request
import re
from bs4 import BeautifulSoup

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

URL = "https://www.reformasthlm.se/sv/sangbord-line-ek-svart"
BACKUP_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-05-29-reforma-cabinet\LINES01_Original_Backup"

def download_file(url, dest_path):
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
        with open(dest_path, 'wb') as f:
            f.write(data)
        print(f"  ✓ Downloaded: {url} -> {dest_path}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to download {url}: {e}")
        return False

def main():
    print("==================================================")
    print("      CREATING ORIGINAL BACKUP FOR LINES01        ")
    print("==================================================")
    
    # Establish subdirectories to mirror FTP structure
    artiklar_dir = os.path.join(BACKUP_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    os.makedirs(artiklar_dir, exist_ok=True)
    os.makedirs(liten_dir, exist_ok=True)
    os.makedirs(zoom_dir, exist_ok=True)
    
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    req = urllib.request.Request(URL, headers=req_headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ Failed to fetch product page: {e}")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    img_tags = soup.find_all('img')
    
    image_paths = []
    for img in img_tags:
        src = img.get('src', '')
        if 'artiklar' in src:
            clean_src = src.split('?')[0]
            if clean_src.startswith('/img/'):
                clean_src = clean_src[4:]
            if clean_src not in image_paths:
                image_paths.append(clean_src)
                
    print(f"Found {len(image_paths)} image assets on product page.")
    
    # Standard images to backup based on Askås patterns
    # Let's search specifically for LINES01 variants
    downloaded_files = 0
    
    # 1. Main Normal
    normal_url = "https://www.reformasthlm.se/bilder/artiklar/LINES01.jpg"
    dest_normal = os.path.join(artiklar_dir, "LINES01.jpg")
    if download_file(normal_url, dest_normal):
        downloaded_files += 1
        
    # 2. Thumbnail
    liten_url = "https://www.reformasthlm.se/bilder/artiklar/liten/LINES01_S.jpg"
    dest_liten = os.path.join(liten_dir, "LINES01_S.jpg")
    if download_file(liten_url, dest_liten):
        downloaded_files += 1
        
    # 3. Zoom Images (Askås usually supports up to 10 images)
    for i in range(1, 11):
        zoom_url = f"https://www.reformasthlm.se/bilder/artiklar/zoom/LINES01_{i}.jpg"
        dest_zoom = os.path.join(zoom_dir, f"LINES01_{i}.jpg")
        
        # Test download
        req_zoom = urllib.request.Request(zoom_url, headers=req_headers)
        try:
            # Check if zoom image exists before downloading
            urllib.request.urlopen(req_zoom, timeout=5)
            # If exists, download it
            if download_file(zoom_url, dest_zoom):
                downloaded_files += 1
        except Exception:
            # If 404/error, then no more zoom images exist
            break
            
    print("\n==================================================")
    print("             BACKUP PROCESS COMPLETE!             ")
    print("==================================================")
    print(f"📂 Backup saved to: {BACKUP_DIR}")
    print(f"  └─ /artiklar/      (Normal, 1000px): {len(os.listdir(artiklar_dir)) - 1} files")
    print(f"  └─ /artiklar/liten/ (Liten, 400px):  {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (Zoom, 2000px):  {len(os.listdir(zoom_dir))} files")
    print(f"✓ Total original images downloaded: {downloaded_files}")
    print("==================================================")

if __name__ == "__main__":
    main()
