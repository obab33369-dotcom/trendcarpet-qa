import os
import sys
import json
import re
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

# Reconfigure stdout/stderr encoding for Windows cp1252 terminal
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"

def get_clean_slug(filename):
    # Remove extension
    base, _ = os.path.splitext(filename)
    # Remove leading ID (e.g. "0338_")
    base = re.sub(r'^\d+_', '', base)
    # Remove Midjourney generation tags (e.g. "-1-26U-wonder", "-1-26u-wonder")
    base = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1-\w+-\w+$', '', base)
    base = re.sub(r'-\d+-\w+-\w+$', '', base)
    return base.strip()

def scrape_specifications(slug):
    url = f"https://www.reformasthlm.se/sv/{urllib.parse.quote(slug)}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', class_='TeknSpec_Tabell')
        if not table:
            return None
            
        specs = {}
        for row in table.find_all('tr'):
            left = row.find(class_=lambda c: c and 'Vanster' in c)
            right = row.find(class_=lambda c: c and 'Hoger' in c)
            if left and right:
                key = left.text.strip().replace(':', '')
                val = right.text.strip()
                specs[key.lower()] = val
        return specs
    except Exception as e:
        # Silently fail or log for debug
        return None

def build_dimension_string(specs):
    if not specs:
        return None
        
    parts = []
    
    # Bredd
    width = specs.get('bredd') or specs.get('width')
    if width:
        parts.append(f"{width.replace(' ', '')} in width")
        
    # Höjd
    height = specs.get('höjd') or specs.get('hojd') or specs.get('height')
    if height:
        parts.append(f"{height.replace(' ', '')} in height")
        
    # Djup / Längd
    depth = specs.get('djup') or specs.get('längd/djup') or specs.get('langd/djup') or specs.get('depth')
    if depth:
        parts.append(f"{depth.replace(' ', '')} in depth")
        
    # Diameter
    diameter = specs.get('diameter')
    if diameter:
        parts.append(f"{diameter.replace(' ', '')} in diameter")
        
    if not parts:
        return None
        
    # Format naturally, e.g. "measuring 80cm in width, 40cm in depth, and 120cm in height"
    if len(parts) == 1:
        return f"measuring {parts[0]}"
    elif len(parts) == 2:
        return f"measuring {parts[0]} and {parts[1]}"
    else:
        return f"measuring {', '.join(parts[:-1])}, and {parts[-1]}"

def main():
    print("==================================================")
    print("      SCRAPING DIMENSIONS FOR STORAGE & LAMPS     ")
    print("==================================================")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}!")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    print(f"Loaded Batch 2 database with {len(db)} items.")
    
    # Identify items to scrape (storage/förvaring and lampa)
    target_keys = []
    for k, v in db.items():
        cat = v.get("metadata", {}).get("typ_av_möbel")
        if cat in ["förvaring", "lampa"]:
            target_keys.append(k)
            
    print(f"Identified {len(target_keys)} storage and lamp items to scrape dimensions for.")
    
    scraped_success = 0
    
    for i, key in enumerate(target_keys):
        slug = get_clean_slug(key)
        print(f"[{i+1}/{len(target_keys)}] Scraping '{slug}'...")
        
        specs = scrape_specifications(slug)
        if specs:
            dim_str = build_dimension_string(specs)
            if dim_str:
                # Add to metadata
                db[key]["metadata"]["dimensions"] = dim_str
                scraped_success += 1
                print(f"   [OK] Dimensions: {dim_str}")
                # Print material if present
                material = specs.get('material')
                if material:
                    print(f"   [INFO] Material: {material}")
            else:
                print("   [WARNING] No dimensional properties found in spec table.")
        else:
            print("   [WARNING] Specs table not found (404 or missing table).")
            
        time.sleep(0.2) # Polite scraping delay
        
    # Write back database
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print("            DIMENSIONS SCRAPING COMPLETE!         ")
    print("==================================================")
    print(f"📝 Database updated with dimensions for {scraped_success} items.")
    print(f"💾 File updated: {DB_PATH}")
    print("==================================================")

if __name__ == "__main__":
    main()
