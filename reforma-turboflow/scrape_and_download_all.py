import os
import sys
import json
import urllib.request
import urllib.parse
import re
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BRAND_DICT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\brand_sku_dict.json"
OUTPUT_IMAGES_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-original-images"
MAPPING_CSV_PATH = os.path.join(OUTPUT_IMAGES_DIR, "brand_sku_map.csv")

def clean_swedish_chars(text):
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text

def extract_sku_from_image_path(path):
    filename = os.path.basename(path)
    base, _ = os.path.splitext(filename)
    # Remove _1, _2, _S suffixes
    base = re.sub(r'_[1-9]$', '', base)
    base = re.sub(r'_S$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'_s$', '', base)
    return base

def download_image(url, dest_path):
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
        with open(dest_path, 'wb') as f:
            f.write(data)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    print("==================================================")
    print("      BACKWARD BRAND SCRAPER & IMAGE DOWNLOADER    ")
    print("==================================================")
    
    os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)
    
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    brand_sku_dict = {}
    
    # 1. Page ranges backwards from page 13 (577-607) down to page 1 (1-48)
    ranges = [
        "577-607",  # Page 13 (last)
        "529-576",  # Page 12
        "481-528",  # Page 11
        "433-480",  # Page 10
        "385-432",  # Page 9
        "337-384",  # Page 8
        "289-336",  # Page 7
        "241-288",  # Page 6
        "193-240",  # Page 5
        "145-192",  # Page 4
        "97-144",   # Page 3
        "49-96",    # Page 2
        "1-48"      # Page 1
    ]
    
    print(f"Scraping {len(ranges)} brand pages in REVERSE order to build catalog list...")
    
    for idx, r in enumerate(ranges):
        url = f"https://www.reformasthlm.se/reforma?visa={r}"
        print(f"  Step {idx+1}/{len(ranges)}: Fetching page range '{r}'...")
        
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            soup = BeautifulSoup(html, 'html.parser')
            img_tags = soup.find_all('img')
            
            page_extracted = 0
            for img in img_tags:
                src = img.get('src', '')
                alt = img.get('alt', '')
                
                # Check for products
                if 'artiklar' in src:
                    # Find link
                    parent_a = img.find_parent('a')
                    href = parent_a.get('href', '') if parent_a else ''
                    
                    if href and '/sv/' in href:
                        slug = href.split('/')[-1].strip().lower()
                        clean_src = src.split('?')[0]
                        if clean_src.startswith('/img/'):
                            clean_src = clean_src[4:]
                            
                        sku = extract_sku_from_image_path(clean_src)
                        
                        if slug not in brand_sku_dict:
                            brand_sku_dict[slug] = {
                                "sku": sku,
                                "name": alt.strip(),
                                "url": f"https://www.reformasthlm.se{href}",
                                "image_path": clean_src
                            }
                            page_extracted += 1
                            
            print(f"    ✓ Extracted {page_extracted} new products (Total gathered so far: {len(brand_sku_dict)})")
            
        except Exception as e:
            print(f"    ❌ Error scraping range {r}: {e}")
            
        time.sleep(0.5)  # Respectful crawl delay
        
    print(f"\n✓ Scraped a total of {len(brand_sku_dict)} unique products from the brand pages!")
    
    # Save master brand dictionary
    with open(BRAND_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(brand_sku_dict, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved Master Brand Dictionary to: {BRAND_DICT_PATH}")
    
    # 2. Download original Image 1 for all products in parallel
    print("\n==================================================")
    print("             DOWNLOADING ORIGINAL IMAGES          ")
    print("==================================================")
    print(f"Downloading images in parallel to: {OUTPUT_IMAGES_DIR}")
    
    download_tasks = []
    for slug, info in brand_sku_dict.items():
        sku = info["sku"]
        rel_img_path = info["image_path"]
        
        # Ensure it has leading slash
        if not rel_img_path.startswith('/'):
            rel_img_path = '/' + rel_img_path
            
        img_url = f"https://www.reformasthlm.se{rel_img_path}"
        
        # Keep original extension from rel_img_path
        _, ext = os.path.splitext(rel_img_path.split('?')[0])
        if not ext:
            ext = '.jpg'
            
        dest_filename = f"{sku}{ext}"
        dest_path = os.path.join(OUTPUT_IMAGES_DIR, dest_filename)
        
        download_tasks.append((img_url, dest_path, sku, info["name"]))
        
    success_count = 0
    fail_count = 0
    
    # Use ThreadPoolExecutor for fast concurrent downloading
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(download_image, task[0], task[1]): task for task in download_tasks
        }
        
        for i, future in enumerate(as_completed(futures)):
            task = futures[future]
            sku = task[2]
            success, err = future.result()
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                print(f"  ❌ Failed to download {sku}: {err}")
                
            if (i + 1) % 50 == 0 or (i + 1) == len(futures):
                print(f"  Progress: {i + 1}/{len(futures)} downloaded ({success_count} success, {fail_count} failed)")
                
    print(f"\n✓ Image downloading complete! Success: {success_count}, Failed: {fail_count}")
    
    # 3. Create a clean CSV mapping file for the user
    print("\n📂 Generating master CSV mapping file...")
    try:
        with open(MAPPING_CSV_PATH, "w", encoding="utf-8-sig") as f:
            f.write("SKU,Product Name,Product URL,Live Image URL,Local Path\n")
            for slug, info in sorted(brand_sku_dict.items(), key=lambda x: x[1]["sku"]):
                sku = info["sku"]
                name = info["name"].replace('"', '""')
                prod_url = info["url"]
                
                rel_img_path = info["image_path"]
                if not rel_img_path.startswith('/'):
                    rel_img_path = '/' + rel_img_path
                img_url = f"https://www.reformasthlm.se{rel_img_path}"
                
                _, ext = os.path.splitext(rel_img_path.split('?')[0])
                if not ext:
                    ext = '.jpg'
                local_path = os.path.join(OUTPUT_IMAGES_DIR, f"{sku}{ext}")
                
                f.write(f'"{sku}","{name}","{prod_url}","{img_url}","{local_path}"\n')
                
        print(f"✓ Saved Master CSV Map to: {MAPPING_CSV_PATH}")
    except Exception as e:
        print(f"❌ Failed to write CSV mapping file: {e}")
        
    print("==================================================")
    print("                 PROCESS COMPLETE!                ")
    print("==================================================")

if __name__ == "__main__":
    main()
