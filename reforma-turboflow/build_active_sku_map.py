import os
import sys
import json
import urllib.request
import urllib.parse
import re
import time
from bs4 import BeautifulSoup

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"
SKU_MAP_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\sku_map.json"
UNRESOLVED_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\unresolved_products.txt"

def clean_swedish_chars(text):
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text

def get_clean_slug(filename):
    base, _ = os.path.splitext(filename)
    base = re.sub(r'^\d+_', '', base)
    base = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1-\w+-\w+$', '', base)
    base = re.sub(r'-\d+-\w+-\w+$', '', base)
    return base.strip()

def should_skip_item(filename: str) -> bool:
    fname = filename.lower()
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    
    # We clean swedish chars to verify cleanly
    def c_str(s):
        repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
        for c, r in repl.items(): s = s.replace(c, r)
        return s.lower()
        
    cleaned_fname = c_str(fname)
    for kw in skip_keywords:
        if kw in fname or c_str(kw) in cleaned_fname:
            return True
    return False

def extract_sku_from_image_path(path):
    filename = os.path.basename(path)
    base, _ = os.path.splitext(filename)
    # Remove _1, _2, _S suffixes
    base = re.sub(r'_[1-9]$', '', base)
    base = re.sub(r'_S$', '', base, flags=re.IGNORECASE)
    return base

def generate_candidate_slugs(raw_slug):
    slug_clean = clean_swedish_chars(raw_slug)
    candidates = [slug_clean, raw_slug]
    
    # Prefix expansions for common words
    # 1. Lamp prefix matching
    if "lampa" in slug_clean:
        base = slug_clean.replace("lampa-", "").replace("-lampa", "")
        candidates.extend([
            f"bordslampa-{base}",
            f"taklampa-{base}",
            f"golvlampa-{base}",
            f"vagglampa-{base}",
            f"pendellampa-{base}"
        ])
    # 2. Seating prefix matching
    if "stol" in slug_clean:
        base = slug_clean.replace("stol-", "").replace("-stol", "")
        candidates.extend([
            f"matstol-{base}",
            f"karmstol-{base}",
            f"pinnstol-{base}",
            f"barstol-{base}"
        ])
    # 3. Sofa prefix matching
    if "soffa" in slug_clean:
        base = slug_clean.replace("soffa-", "").replace("-soffa", "")
        candidates.extend([
            f"3-sitssoffa-{base}",
            f"2-sitssoffa-{base}",
            f"baddsoffa-{base}"
        ])
    # 4. Table prefix matching
    if "bord" in slug_clean:
        base = slug_clean.replace("bord-", "").replace("-bord", "")
        candidates.extend([
            f"matbord-{base}",
            f"soffbord-{base}",
            f"sidobord-{base}"
        ])
        
    # Unique candidates list preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)
            
    return unique_candidates

def main():
    print("==================================================")
    print("      BUILDING ACTIVE PRODUCT SKU MAP & IMAGES    ")
    print("==================================================")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}!")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    # Filter active keys
    active_keys = sorted([k for k in db.keys() if not should_skip_item(k)])
    print(f"Total products in DB: {len(db)}")
    print(f"Total active products (excluding skips): {len(active_keys)}")
    
    sku_map = {}
    unresolved = []
    
    # Load existing map if exists to support resuming
    if os.path.exists(SKU_MAP_PATH):
        try:
            with open(SKU_MAP_PATH, "r", encoding="utf-8") as f:
                sku_map = json.load(f)
            print(f"Loaded existing SKU map with {len(sku_map)} mapped items.")
        except Exception:
            pass
            
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    success_count = 0
    skipped_mapping = 0
    
    for idx, key in enumerate(active_keys):
        # Skip if already mapped
        if key in sku_map and sku_map[key].get("sku"):
            skipped_mapping += 1
            continue
            
        raw_slug = get_clean_slug(key)
        candidates = generate_candidate_slugs(raw_slug)
        
        print(f"[{idx+1}/{len(active_keys)}] Resolving '{raw_slug}'...")
        
        resolved = False
        for cand in candidates:
            url = f"https://www.reformasthlm.se/sv/{urllib.parse.quote(cand)}"
            req = urllib.request.Request(url, headers=req_headers)
            
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check for product image tags
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
                            
                if image_paths:
                    sku = extract_sku_from_image_path(image_paths[0])
                    sku_map[key] = {
                        "sku": sku,
                        "slug": cand,
                        "url": url,
                        "current_images": image_paths
                    }
                    print(f"   [SUCCESS] SKU: '{sku}' | Live URL: {url} ({len(image_paths)} images)")
                    resolved = True
                    success_count += 1
                    break
            except Exception:
                continue
                
        if not resolved:
            print(f"   [FAILED] Could not resolve any candidate slugs for '{raw_slug}'")
            unresolved.append(key)
            
        # Write mapping back progressively to avoid losing progress
        with open(SKU_MAP_PATH, "w", encoding="utf-8") as f:
            json.dump(sku_map, f, ensure_ascii=False, indent=2)
            
        time.sleep(0.2)  # Polite delay
        
    # Write unresolved keys
    with open(UNRESOLVED_PATH, "w", encoding="utf-8") as f:
        for k in unresolved:
            f.write(k + "\n")
            
    print("\n==================================================")
    print("             MAPPING PROCESS COMPLETE!            ")
    print("==================================================")
    print(f"🗃️ Total active items: {len(active_keys)}")
    print(f"✓ Already mapped (skipped): {skipped_mapping}")
    print(f"✓ Successfully mapped in this run: {success_count}")
    print(f"⚠️ Unresolved items: {len(unresolved)}")
    print(f"💾 Map saved to: {SKU_MAP_PATH}")
    print(f"💾 Unresolved list saved to: {UNRESOLVED_PATH}")
    print("==================================================")

if __name__ == "__main__":
    main()
