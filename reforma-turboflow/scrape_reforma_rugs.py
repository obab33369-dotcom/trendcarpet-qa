import os
import sys
import json
import time
import io
import re
import urllib.request
from bs4 import BeautifulSoup
from PIL import Image

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
RUGS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_rugs"

def slugify(text):
    text = text.lower().strip()
    # Replace Swedish characters
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    # Remove quotes, apostrophes, parentheses
    text = re.sub(r"['\"()åäöÅÄÖ]", "", text)
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Remove leading/trailing hyphens
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
    # Decode using latin-1 to preserve Swedish characters properly
    html = html_bytes.decode('latin-1')
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
    print("=== REFORMA STOCKHOLM RUG SCRAPER ===")
    
    # 1. Fetch products from Page 1 and Page 2
    all_scraped_products = []
    seen_hrefs = set()
    
    pages = [
        "https://www.reformasthlm.se/sv/inredning/mattor",
        "https://www.reformasthlm.se/sv/inredning/mattor?page=2"
    ]
    
    for page_url in pages:
        try:
            html_bytes = fetch_url(page_url)
            page_products = parse_page_products(html_bytes)
            print(f"Parsed {len(page_products)} products from {page_url}")
            
            for p in page_products:
                if p['href'] not in seen_hrefs:
                    seen_hrefs.add(p['href'])
                    all_scraped_products.append(p)
            time.sleep(1) # Polite delay
        except Exception as e:
            print(f"Error fetching page {page_url}: {e}")
            
    print(f"Total unique products found: {len(all_scraped_products)}")
    
    if len(all_scraped_products) < 50:
        print("Warning: Found fewer than 50 rugs. We will process all that we found.")
        target_count = len(all_scraped_products)
    else:
        target_count = 50
        
    target_products = all_scraped_products[:target_count]
    print(f"Processing first {target_count} rugs...")
    
    # 2. Setup download folder
    os.makedirs(RUGS_DIR, exist_ok=True)
    print(f"Target directory for rug assets: {RUGS_DIR}")
    
    # Load database to append
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            database = json.load(f)
        print(f"Loaded existing database with {len(database)} items.")
    else:
        database = {}
        print("Database not found! Creating new database dictionary.")
        
    # Track newly added items
    added_count = 0
    
    # Styles to cycle through for diversity
    styles = ["nordisk modern", "minimalistisk", "sekelskifte"]
    
    # Clean up existing rugs in database (optional, but let's append fresh)
    # To be clean, let's delete any old keys starting with "20" and ending with "matta" to avoid cluttering in multiple runs
    keys_to_delete = [k for k in database.keys() if k.startswith("20") and database[k]["metadata"]["typ_av_möbel"] == "matta"]
    for k in keys_to_delete:
        del database[k]
    if keys_to_delete:
        print(f"Cleared {len(keys_to_delete)} old rug entries from database to ensure fresh run.")
        
    for index, p in enumerate(target_products):
        id_num = 2001 + index
        orig_title = p['title']
        clean_title = orig_title
        slug = slugify(clean_title)
        
        # Unique filename
        filename = f"{id_num}_{slug}.webp"
        
        # Image URL
        img_src = p['img_src']
        # Strip query parameters (like ?m=1774010867) to get clean image url
        clean_img_path = img_src.split('?')[0]
        if not clean_img_path.startswith('http'):
            img_url = "https://www.reformasthlm.se" + clean_img_path
        else:
            img_url = clean_img_path
            
        print(f"[{index+1}/{target_count}] Downloading {orig_title} -> {filename}...")
        
        # Download and convert to WebP
        success = False
        try:
            req = urllib.request.Request(
                img_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=15) as img_resp:
                img_data = img_resp.read()
                
            # Convert to WebP using Pillow
            image = Image.open(io.BytesIO(img_data))
            dest_path = os.path.join(RUGS_DIR, filename)
            image.save(dest_path, "WEBP", quality=90)
            
            # Determine properties for metadata
            lower_title = clean_title.lower()
            
            # Shape
            if any(x in lower_title for x in ["rund", "cirkel", "cirkulär", "round"]):
                form = "rund"
            else:
                form = "rektangulär"
                
            # Tyg material
            if "jute" in lower_title:
                material = "jute"
            elif "ull" in lower_title:
                material = "ull"
            elif "bomull" in lower_title:
                material = "bomull"
            elif "trasmatta" in lower_title:
                material = "bomull"
            elif "viskos" in lower_title:
                material = "viskos"
            else:
                material = "ull" # Default
                
            # Color tone
            # Cool color keywords
            cool_keywords = ["grå", "gra", "grön", "gron", "blå", "bla", "svart", "silver", "kall", "antracit", "mörkgrå"]
            if any(x in lower_title for x in cool_keywords):
                tone = "kall"
            else:
                tone = "varm" # Most rugs are warm (beige, sand, natur, creme)
                
            # Estetik
            estetik = styles[index % len(styles)]
            
            # Save into database
            database[filename] = {
                "filename": filename,
                "parsed_name": clean_title,
                "metadata": {
                    "typ_av_möbel": "matta",
                    "träslag": "inget", # bypass wood harmony
                    "tyg_material": material,
                    "färgton": tone,
                    "stil_estetik": estetik,
                    "form": form
                },
                "timestamp": time.time()
            }
            success = True
            added_count += 1
            print(f"  ✓ Success! Shape: {form}, Material: {material}, Tone: {tone}, Estetik: {estetik}")
        except Exception as e:
            print(f"  ✗ Failed to download/process {img_url}: {e}")
            
        time.sleep(0.5) # Polite delay between downloads
        
    # Write back database
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
        
    print("\n=== SCRAPING COMPLETE ===")
    print(f"Successfully downloaded and registered {added_count} rugs in database!")
    print(f"Updated database file at: {DB_PATH}")

if __name__ == "__main__":
    main()
