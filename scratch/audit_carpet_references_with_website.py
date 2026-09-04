import os
import json
import base64
import requests
import re
import shutil
import time
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
BRAIN_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"
AUDIT_IMAGES_DIR = os.path.join(BRAIN_DIR, "audit_images")
GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

os.makedirs(AUDIT_IMAGES_DIR, exist_ok=True)

def load_gemini_key():
    if os.path.exists(GEMINI_KEY_PATH):
        with open(GEMINI_KEY_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

API_KEY = load_gemini_key()

def encode_image(img_path, max_size=600):
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((max_size, max_size))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=80)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding {img_path}: {e}")
        return None

def download_image(url, dest_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            with open(dest_path, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        pass
    return False

def scrape_og_image(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            html = r.text
            m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            if m:
                return m.group(1)
    except Exception as e:
        pass
    return None

def compute_mae(img1_path, img2_path):
    try:
        img1 = Image.open(img1_path).convert('L').resize((256, 256))
        img2 = Image.open(img2_path).convert('L').resize((256, 256))
        
        pixels1 = list(img1.getdata())
        pixels2 = list(img2.getdata())
        
        diff = sum(abs(p1 - p2) for p1, p2 in zip(pixels1, pixels2))
        mae = diff / (256 * 256)
        return mae
    except Exception as e:
        print(f"Error calculating MAE: {e}")
        return None

def compute_ahash(img_path):
    try:
        try:
            resampling = Image.Resampling.LANCZOS
        except AttributeError:
            resampling = Image.LANCZOS
        img = Image.open(img_path).convert('L').resize((8, 8), resampling)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        hash_bits = [1 if p >= avg else 0 for p in pixels]
        return hash_bits
    except Exception:
        return None

def hamming_distance(hash1, hash2):
    if not hash1 or not hash2:
        return 999
    return sum(b1 != b2 for b1, b2 in zip(hash1, hash2))

def compare_images_gemini(local_path, web_path, sku, folder_name):
    if not API_KEY:
        return {"error": "No API Key"}
        
    local_b64 = encode_image(local_path)
    web_b64 = encode_image(web_path)
    
    if not local_b64 or not web_b64:
        return {"error": "Failed to encode images"}
        
    parts = [
        {"text": f"You are a quality control agent auditing product catalog reference images.\nSKU: {sku}\nFolder Name: {folder_name}\n\nBelow are two images:\n"},
        {"text": "Image 1: Reference image found on disk (local):\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": local_b64}},
        {"text": "\nImage 2: Official product image downloaded from Reforma's live website (web):\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": web_b64}},
        {"text": "\nYour task is to determine if these two images visually represent the exact same carpet design and color.\n\nCompare them very carefully:\n- Look at the pattern (e.g. checkered, diamonds, solid, circles, organic shapes).\n- Look at the colors.\n- Look at the edges/border style.\n\nReturn your response strictly as a JSON object with two keys:\n- 'match': true (if they represent the same design and color) or false (if they show different designs/colors, or if one is completely wrong).\n- 'explanation': A detailed explanation of your findings in Swedish, pointing out exactly what is different (or confirming they match).\n"}
    ]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }
    
    # Retry loop for rate limiting
    for attempt in range(4):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=60)
            if res.status_code == 200:
                result_json = res.json()['candidates'][0]['content']['parts'][0]['text']
                return json.loads(result_json)
            elif res.status_code == 429:
                # Rate limit hit, sleep and retry
                time.sleep(2 ** attempt + 2)
            else:
                return {"error": f"API error {res.status_code}"}
        except Exception as e:
            if attempt == 3:
                return {"error": str(e)}
            time.sleep(1)
    return {"error": "Max retries exceeded"}

def audit_sku(sku, info, brand_dict, sku_map):
    folder_name = info["folder_name"]
    local_ref_path = info["ref_path"]
    
    # Check if local reference exists
    if not os.path.exists(local_ref_path):
        # Fallback to the -NEW suffix folder if it was run
        fallback_path = local_ref_path.replace("Reforma-Mattor-sortering", "Reforma-Mattor-sortering-NEW")
        if os.path.exists(fallback_path):
            local_ref_path = fallback_path
        else:
            return {"sku": sku, "folder_name": folder_name, "status": "ERROR", "details": "Local reference file missing"}

    # Copy local reference to audit folder for markdown embedding
    shutil.copy2(local_ref_path, os.path.join(AUDIT_IMAGES_DIR, f"local_{sku}.jpg"))
    
    # Get live product URL
    url = None
    for slug, b_info in brand_dict.items():
        if b_info.get('sku') == sku:
            url = b_info.get('url')
            break
            
    if not url:
        for k, s_info in sku_map.items():
            if s_info.get('sku') == sku:
                url = s_info.get('url')
                break
                
    if not url:
        clean_name = folder_name.split(' (')[0].lower()
        clean_name = clean_name.replace("å", "a").replace("ä", "a").replace("ö", "o").replace(" ", "-")
        url = f"https://www.reformasthlm.se/sv/{clean_name}"

    # Try to get live image URL
    img_url = scrape_og_image(url)
    if not img_url:
        fallback_url = f"https://www.reformasthlm.se/sv/{sku.lower()}"
        img_url = scrape_og_image(fallback_url)
    if not img_url:
        img_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}.jpg"
        
    web_dest_path = os.path.join(AUDIT_IMAGES_DIR, f"web_{sku}.jpg")
    
    # Download web image
    download_success = download_image(img_url, web_dest_path)
    if not download_success:
        img_url_png = img_url.replace(".jpg", ".png")
        download_success = download_image(img_url_png, web_dest_path)
        
    if not download_success:
        return {"sku": sku, "folder_name": folder_name, "status": "ERROR", "details": f"Failed to download web image from {img_url}"}
        
    # Run comparison: try fast pixel checks first
    mae = compute_mae(local_ref_path, web_dest_path)
    hash1 = compute_ahash(local_ref_path)
    hash2 = compute_ahash(web_dest_path)
    h_dist = hamming_distance(hash1, hash2)
    
    # Thresholds: if MAE < 5.0 or Hamming distance <= 2, we consider them identical
    is_pixel_match = False
    if mae is not None and mae < 5.0:
        is_pixel_match = True
    elif h_dist <= 2:
        is_pixel_match = True
        
    if is_pixel_match:
        comparison = {
            "match": True,
            "explanation": f"Bilder matchade exakt via pixel-nivå analys (MAE: {f'{mae:.2f}' if mae is not None else 'N/A'}, Hamming-avstånd: {h_dist}/64)."
        }
    else:
        # Fall back to Gemini API
        comparison = compare_images_gemini(local_ref_path, web_dest_path, sku, folder_name)
    
    if "error" in comparison:
        return {"sku": sku, "folder_name": folder_name, "status": "ERROR", "details": comparison["error"]}
        
    match = comparison.get("match", False)
    explanation = comparison.get("explanation", "")
    
    return {
        "sku": sku,
        "folder_name": folder_name,
        "status": "MATCH" if match else "MISMATCH",
        "explanation": explanation,
        "local_img": f"audit_images/local_{sku}.jpg",
        "web_img": f"audit_images/web_{sku}.jpg"
    }

def main():
    catalog_path = os.path.join(PROJECT_DIR, "scratch", "carpet_catalog.json")
    brand_dict_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
    sku_map_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'sku_map.json')
    
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    with open(brand_dict_path, 'r', encoding='utf-8') as f:
        brand_dict = json.load(f)
    with open(sku_map_path, 'r', encoding='utf-8') as f:
        sku_map = json.load(f)
        
    print(f"Starting product-level visual audit for {len(catalog)} carpets...")
    
    results = []
    
    # We will use ThreadPoolExecutor to run comparisons concurrently but with limited workers to avoid rate limits
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(audit_sku, sku, info, brand_dict, sku_map): sku for sku, info in catalog.items()}
        
        completed = 0
        for future in as_completed(futures):
            sku = futures[future]
            try:
                res = future.result()
                results.append(res)
                completed += 1
                print(f"[{completed}/{len(catalog)}] Audited {sku}: {res['status']}")
            except Exception as e:
                print(f"Error auditing {sku}: {e}")
                results.append({"sku": sku, "folder_name": sku, "status": "ERROR", "details": str(e)})
                
    # Save raw results
    with open(os.path.join(PROJECT_DIR, "scratch", "carpet_audit_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # Generate Markdown Report
    matches = [r for r in results if r["status"] == "MATCH"]
    mismatches = [r for r in results if r["status"] == "MISMATCH"]
    errors = [r for r in results if r["status"] == "ERROR"]
    
    report_path = os.path.join(BRAIN_DIR, "carpet_product_level_audit.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Produktanalys: Granskning av Mattor på Produktnivå mot Hemsidan\n\n")
        f.write("Vi har jämfört alla våra lokala referensbilder (som användes under generering och sortering) med produktbilderna från Reformas hemsida.\n\n")
        
        f.write("## Sammanfattning av Granskningen\n\n")
        f.write(f"- **Totalt granskade mattor**: {len(results)}\n")
        f.write(f"- **Korrekt matchade (OK)**: {len(matches)}\n")
        f.write(f"- **Felaktiga källbilder (Mismatches)**: {len(mismatches)}\n")
        f.write(f"- **Fel under granskningen (Errors)**: {len(errors)}\n\n")
        
        f.write("## 🚩 Avvikande Mattor (Mismatches)\n\n")
        f.write("Följande mattor har felaktiga källbilder lokalt jämfört med hemsidan:\n\n")
        
        for idx, item in enumerate(mismatches):
            sku = item["sku"]
            f.write(f"### {idx+1}. {item['folder_name']} (SKU: {sku})\n\n")
            f.write(f"**AI Analys:** {item['explanation']}\n\n")
            f.write("| Lokal referensbild (på disk) | Officiell bild från hemsidan |\n")
            f.write("| :---: | :---: |\n")
            f.write(f"| ![{sku} lokal]({item['local_img']}) | ![{sku} web]({item['web_img']}) |\n\n")
            f.write("---\n\n")
            
        f.write("## 🟢 Korrekt Matchade Mattor (Match)\n\n")
        f.write("| SKU | Mappnamn | Beskrivning |\n")
        f.write("|---|---|---|\n")
        for item in matches:
            f.write(f"| `{item['sku']}` | {item['folder_name']} | {item['explanation'][:100]}... |\n")
            
        if errors:
            f.write("\n## ⚠️ Misslyckade Granskningar (Errors)\n\n")
            for item in errors:
                f.write(f"- **SKU {item['sku']}**: {item.get('details', 'Okänt fel')}\n")
                
    print(f"\nAudit complete! Report saved to {report_path}")

if __name__ == "__main__":
    main()
