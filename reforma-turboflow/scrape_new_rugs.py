import os
import sys
import json
import time
import io
import re
import urllib.request
from bs4 import BeautifulSoup
from PIL import Image

# Reconfigure stdout/stderr encoding for Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB1_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
NEW_RUGS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\new_rugs"
NEW_RUGS_DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\new_rugs_db.json"

def slugify(text):
    text = text.lower().strip()
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    text = re.sub(r"['\"()åäöÅÄÖ]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip('-')
    return text

def fetch_url(url):
    print(f"Fetching: {url}")
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()

def parse_page_products(html_bytes):
    html = html_bytes.decode('latin-1') # Preserve Swedish chars
    soup = BeautifulSoup(html, 'html.parser')
    
    product_anchors = soup.find_all('a', class_=lambda c: c and 'img-slider' in c)
    products = []
    
    for a in product_anchors:
        title = a.get('aria-label') or a.get('title')
        href = a.get('href')
        img = a.find('img')
        img_src = img.get('src') if img else None
        
        if not title and img:
            title = img.get('alt') or img.get('title')
            
        if title and href and img_src:
            products.append({
                'title': title.strip(),
                'href': href.strip(),
                'img_src': img_src.strip()
            })
    return products

def main():
    print("==================================================")
    print("      SCRAPING NEW UNIQUE RUGS FROM REFORMA       ")
    print("==================================================")
    
    # 1. Load used rugs from Batch 1 DB to avoid duplicates
    used_titles = set()
    used_slugs = set()
    if os.path.exists(DB1_PATH):
        with open(DB1_PATH, "r", encoding="utf-8") as f:
            db1 = json.load(f)
        for k, v in db1.items():
            if v.get("metadata", {}).get("typ_av_möbel") == "matta":
                used_titles.add(v["parsed_name"].lower())
                slug = k.split('_', 1)[-1]
                used_slugs.add(slugify(slug))
        print(f"Loaded {len(used_titles)} already used rugs from Batch 1 to skip.")
    
    # 2. Fetch unique products from pages 3 to 10
    all_scraped_products = []
    seen_hrefs = set()
    
    # Scrape pages 3 to 10 (wider range to get enough new items)
    pages = [f"https://www.reformasthlm.se/sv/inredning/mattor?page={i}" for i in range(3, 11)]
    
    for page_url in pages:
        try:
            html_bytes = fetch_url(page_url)
            page_products = parse_page_products(html_bytes)
            print(f"   Parsed {len(page_products)} products on page.")
            
            for p in page_products:
                if p['href'] not in seen_hrefs:
                    seen_hrefs.add(p['href'])
                    
                    # Filter out old rugs by title and slug
                    title_lower = p['title'].lower()
                    slug = slugify(p['title'])
                    
                    is_duplicate = False
                    for t in used_titles:
                        if t in title_lower or title_lower in t:
                            is_duplicate = True
                            break
                    for s in used_slugs:
                        if s in slug or slug in s:
                            is_duplicate = True
                            break
                            
                    if is_duplicate:
                        continue
                        
                    all_scraped_products.append(p)
            time.sleep(0.5)
        except Exception as e:
            print(f"   Error fetching {page_url}: {e}")
            
    print(f"\nFound {len(all_scraped_products)} NEW unique rugs after filtering out Batch 1!")
    
    if not all_scraped_products:
        print("❌ Error: No new rugs found!")
        return
        
    os.makedirs(NEW_RUGS_DIR, exist_ok=True)
    new_db = {}
    
    styles = ["nordisk modern", "minimalistisk", "sekelskifte"]
    target_count = min(35, len(all_scraped_products))
    print(f"Downloading first {target_count} rugs...")
    
    downloaded_count = 0
    
    for index in range(target_count):
        p = all_scraped_products[index]
        id_num = 3001 + downloaded_count
        orig_title = p['title']
        slug = slugify(orig_title)
        
        filename = f"{id_num:04d}_{slug}.png"
        
        img_src = p['img_src']
        clean_img_path = img_src.split('?')[0]
        if not clean_img_path.startswith('http'):
            img_url = "https://www.reformasthlm.se" + clean_img_path
        else:
            img_url = clean_img_path
            
        print(f"[{downloaded_count+1}/{target_count}] Downloading {orig_title}...")
        
        try:
            req = urllib.request.Request(
                img_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=15) as img_resp:
                img_data = img_resp.read()
                
            # Convert and save directly as PNG
            image = Image.open(io.BytesIO(img_data))
            dest_path = os.path.join(NEW_RUGS_DIR, filename)
            image.save(dest_path, "PNG")
            
            # Determine properties
            lower_title = orig_title.lower()
            if any(x in lower_title for x in ["rund", "cirkel", "cirkulär", "round"]):
                form = "rund"
            else:
                form = "rektangulär"
                
            if "jute" in lower_title:
                material = "jute"
            elif "ull" in lower_title:
                material = "ull"
            elif "bomull" in lower_title or "trasmatta" in lower_title:
                material = "bomull"
            elif "viskos" in lower_title:
                material = "viskos"
            else:
                material = "ull"
                
            cool_keywords = ["grå", "gra", "grön", "gron", "blå", "bla", "svart", "silver", "kall", "antracit", "mörkgrå"]
            if any(x in lower_title for x in cool_keywords):
                tone = "kall"
            else:
                tone = "varm"
                
            estetik = styles[downloaded_count % len(styles)]
            
            new_db[filename] = {
                "filename": filename,
                "parsed_name": orig_title,
                "metadata": {
                    "typ_av_möbel": "matta",
                    "träslag": "inget",
                    "tyg_material": material,
                    "färgton": tone,
                    "stil_estetik": estetik,
                    "form": form
                },
                "timestamp": time.time()
            }
            downloaded_count += 1
            print(f"   [OK] Shape: {form}, Material: {material}, Tone: {tone}")
        except Exception as e:
            print(f"   [ERROR] Failed: {e}")
            
        time.sleep(0.5)
        
    with open(NEW_RUGS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(new_db, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print("             RUG SCRAPING COMPLETE!               ")
    print("==================================================")
    print(f"📂 Downloaded and converted (PNG): {downloaded_count} new rugs.")
    print(f"📝 Database saved: {NEW_RUGS_DB_PATH}")
    print("==================================================")

if __name__ == "__main__":
    main()
