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
BRAND_DICT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\brand_sku_dict.json"

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

def extract_keywords_from_key(key):
    base, _ = os.path.splitext(key)
    base = re.sub(r'^\d+_', '', base)
    base = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1-\w+-\w+$', '', base)
    base = re.sub(r'-\d+-\w+-\w+$', '', base)
    
    parts = base.split('-')
    keywords = []
    for p in parts:
        p_clean = clean_swedish_chars(p.lower().strip())
        if re.match(r'^\d+px$|^\d+cm$|^\d+$', p_clean):
            continue
        if p_clean in ('1', '2', '3', '4', 's', 'l', 'pack', 'med', 'inkl', 'och'):
            continue
        if len(p_clean) >= 3:
            keywords.append(p_clean)
    return keywords

def extract_sku_from_image_path(path):
    filename = os.path.basename(path)
    base, _ = os.path.splitext(filename)
    base = re.sub(r'_[1-9]$', '', base)
    base = re.sub(r'_S$', '', base, flags=re.IGNORECASE)
    return base

def main():
    print("==================================================")
    print("      SCRAPING 607 BRAND PRODUCTS & SKUs          ")
    print("==================================================")
    
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    brand_sku_dict = {}
    
    # 1. Scrape all 15 pages of Reforma's own brand furniture
    # Product range is roughly 1 to 720 (covering 607 articles)
    step = 48
    max_items = 720
    ranges = []
    for start in range(1, max_items, step):
        end = start + step - 1
        ranges.append(f"{start}-{end}")
        
    print(f"Scraping {len(ranges)} pages to gather all product images...")
    
    for idx, r in enumerate(ranges):
        url = f"https://www.reformasthlm.se/reforma?visa={r}"
        print(f"  Page {idx+1}/{len(ranges)}: Fetching range '{r}'...")
        
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            soup = BeautifulSoup(html, 'html.parser')
            img_tags = soup.find_all('img')
            
            page_extracted = 0
            for img in img_tags:
                src = img.get('src', '')
                alt = img.get('alt', '')
                if 'artiklar' in src:
                    # Parse product link
                    parent_a = img.find_parent('a')
                    href = parent_a.get('href', '') if parent_a else ''
                    
                    if href and '/sv/' in href:
                        slug = href.split('/')[-1].strip().lower()
                        # Clean image path
                        clean_src = src.split('?')[0]
                        if clean_src.startswith('/img/'):
                            clean_src = clean_src[4:]
                            
                        sku = extract_sku_from_image_path(clean_src)
                        
                        if slug not in brand_sku_dict:
                            brand_sku_dict[slug] = {
                                "sku": sku,
                                "name": clean_swedish_chars(alt),
                                "url": f"https://www.reformasthlm.se{href}",
                                "image_path": clean_src
                            }
                            page_extracted += 1
                            
            print(f"    ✓ Extracted {page_extracted} new products (Total collected: {len(brand_sku_dict)})")
            
        except Exception as e:
            print(f"    ❌ Error scraping page: {e}")
            
        time.sleep(0.3)  # Polite crawling delay
        
    print(f"\n✓ Scraped a total of {len(brand_sku_dict)} unique products from the brand pages!")
    
    # Save the master brand dictionary
    with open(BRAND_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(brand_sku_dict, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved Master Brand Dictionary to: {BRAND_DICT_PATH}")
    
    # 2. Map active Batch 2 items against the master brand dictionary
    print("\n📂 Step 3: Mapping active Batch 2 items locally...")
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}!")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    # Get active keys (excluding skips)
    active_keys = sorted([k for k in db.keys() if not should_skip_item(k)])
    
    # Load current map if exists to merge
    sku_map = {}
    if os.path.exists(SKU_MAP_PATH):
        try:
            with open(SKU_MAP_PATH, "r", encoding="utf-8") as f:
                sku_map = json.load(f)
        except Exception:
            pass
            
    mapped_count = 0
    newly_mapped_count = 0
    
    for key in active_keys:
        # Reconstruct clean slug
        raw_slug = get_clean_slug(key)
        slug_clean = clean_swedish_chars(raw_slug)
        
        # 1. Direct match in scraped dictionary
        matched_info = brand_sku_dict.get(slug_clean) or brand_sku_dict.get(raw_slug)
        
        # 2. Fuzzy Keyword match if direct fails
        if not matched_info:
            keywords = extract_keywords_from_key(key)
            if keywords:
                # Look for a key in brand_sku_dict that contains all keywords
                best_match_key = None
                best_match_score = 0
                for brand_slug in brand_sku_dict.keys():
                    match_score = sum(1 for kw in keywords if kw in brand_slug)
                    if match_score == len(keywords):
                        best_match_key = brand_slug
                        break
                    elif match_score >= max(1, len(keywords) - 1) and match_score > best_match_score:
                        best_match_score = match_score
                        best_match_key = brand_slug
                        
                if best_match_key:
                    matched_info = brand_sku_dict[best_match_key]
                    
        # 3. Apply mapping if matched
        if matched_info:
            sku_map[key] = {
                "sku": matched_info["sku"],
                "slug": matched_info["slug"] if "slug" in matched_info else os.path.basename(matched_info["url"]),
                "url": matched_info["url"],
                "current_images": [matched_info["image_path"]]
            }
            mapped_count += 1
            if key not in sku_map:
                newly_mapped_count += 1
                
    # Save the updated map
    with open(SKU_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(sku_map, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print("             LOCAL ACTIVE MAPPING COMPLETE        ")
    print("==================================================")
    print(f"🗃️ Total active items: {len(active_keys)}")
    print(f"✓ Mapped active items: {mapped_count} ({(mapped_count/len(active_keys))*100:.1f}% coverage)")
    print(f"💾 Map updated and saved to: {SKU_MAP_PATH}")
    print("==================================================")

def should_skip_item(filename: str) -> bool:
    fname = filename.lower()
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    
    def c_str(s):
        repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
        for c, r in repl.items(): s = s.replace(c, r)
        return s.lower()
        
    cleaned_fname = c_str(fname)
    for kw in skip_keywords:
        if kw in fname or c_str(kw) in cleaned_fname:
            return True
    return False

if __name__ == "__main__":
    main()
