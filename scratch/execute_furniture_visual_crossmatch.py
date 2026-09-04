import os
import json
import base64
import requests
import re
import urllib.parse
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

# Target folders (actual folder names on OneDrive)
TARGET_FOLDERS = [
    "Barstol Forshaga - Silver (KS-01-M-silver)",
    "Barstol Forshaga - SilverNatur (KS-01-W-wood)",
    "Matbord Örsjö Runt 105cm - Natur (91517)",
    "Matgrupp Hornstull Forma 1 Bord & 4 Stolar (matgrupp28)",
    "Matgrupp Kungsholmen Hornstull - 1 Bord & 4 Stolar (matgrupp7)",
    "Matgrupp Kungsholmen Montmartre - 1 Bord & 4 Stolar (matgrupp26)",
    "Matgrupp Marbelous Elsa - 1 Bord ø120 & 6 Stolar (matgrupp17)",
    "Matgrupp Nordisk Elsa - 1 Bord & 4 Stolar (matgrupp42)",
    "Matgrupp Runt Kungsholmen - 1 Bord & 4 Stolar (matgrupp23)",
    "Matgrupp Vega Elsa - 1 Bord & 6 Stolar (matgrupp51)",
    "Sängbord Haninge - Vit (96292)",
    "Sängbord Sand - Ek (08-natural)",
    "Sängbord Sapporo - NaturMetall - Reforma Sthlm (9375%20Oak)",
    "Sängbord Twine - ValnötSvart (21703-walnut)",
    "Tv-bänk Lövhamn L- Natur (2502-natur)",
    "Tv-bänk Myshult 160x55cm - Natur (2372-1-natur)",
    "Vägghylla Joliet - Svart (89382)"
]

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

def encode_image(img_path, max_size=800):
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((max_size, max_size))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception:
        return None

# Import database loading and resolve_anchor functions
import sys
sys.path.append(PROJECT_DIR)
sys.path.append(os.path.join(PROJECT_DIR, "scratch"))
try:
    from rebuild_all_by_time import resolve_anchor, load_db
except Exception as e:
    print(f"Error importing helper functions: {e}")
    resolve_anchor = None
    load_db = None

def main():
    print("=== Executing Visual Cross-Matching Loop for Furniture ===")
    
    if not API_KEY:
        print("Error: Gemini API Key not found!")
        return
        
    # Load catalog
    catalog_path = os.path.join(PROJECT_DIR, "scratch", "furniture_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    # Load prompt databases
    batch1 = load_db("rooms_turboflow_batch1.json") if load_db else {}
    batch2 = load_db("rooms_turboflow_batch2.json") if load_db else {}
    full_catalog = load_db("rooms_turboflow_full_catalog.json") if load_db else {}
    
    # Combined DB mapping
    db_mapping = {}
    db_mapping.update(batch1)
    db_mapping.update(batch2)
    db_mapping.update(full_catalog)
    
    print(f"Loaded {len(db_mapping)} prompt definitions.")
    
    # Collect all rendering files in the target folders on OneDrive discard root
    renders_to_process = []
    
    for folder in TARGET_FOLDERS:
        folder_path = os.path.join(DISCARD_ROOT, folder)
        if not os.path.exists(folder_path):
            print(f"Warning: target folder {folder} not found in discard root.")
            continue
            
        # Add main files
        for f in os.listdir(folder_path):
            f_path = os.path.join(folder_path, f)
            if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                renders_to_process.append({
                    "orig_folder": folder,
                    "filename": f,
                    "path": f_path,
                    "in_reserv": False
                })
                
        # Add reserv files
        reserv_path = os.path.join(folder_path, "reserv")
        if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
            for f in os.listdir(reserv_path):
                f_path = os.path.join(reserv_path, f)
                if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    renders_to_process.append({
                        "orig_folder": folder,
                        "filename": f,
                        "path": f_path,
                        "in_reserv": True
                    })
                    
    print(f"Found {len(renders_to_process)} renderings to cross-match.")
    
    # Process each render
    redirection_plan = {}
    
    def process_render(item):
        orig_folder = item["orig_folder"]
        fn = item["filename"]
        path = item["path"]
        in_reserv = item["in_reserv"]
        
        # 1. Parse prefix
        m = re.match(r"^(\d+)", fn)
        if not m:
            return orig_folder, fn, {"error": "No prefix index in filename"}
            
        prefix = int(m.group(1))
        
        # 2. Look up in DB
        if prefix not in db_mapping:
            return orig_folder, fn, {"error": f"Prefix {prefix} not found in prompt databases"}
            
        refs = db_mapping[prefix]["refs"]
        
        # 3. Resolve to SKUs and filter by furniture catalog
        candidates = []
        for ref in refs:
            if resolve_anchor:
                sku, name = resolve_anchor(ref)
                if sku and sku in catalog:
                    candidates.append({
                        "sku": sku,
                        "name": name,
                        "folder_name": catalog[sku]["folder_name"],
                        "ref_path": catalog[sku]["ref_path"]
                    })
                    
        if not candidates:
            return orig_folder, fn, {"error": f"No candidate furniture products resolved for refs: {refs}"}
            
        # If there's only 1 furniture candidate, let's verify if we need to call Gemini or if we can automatically map it.
        # But wait, to be 100% safe and verify visual presence (or if it's a mismatch where even the database candidate is wrong),
        # let's use Gemini to choose between candidates, or confirm if the single candidate matches.
        
        # Call Gemini comparison
        render_b64 = encode_image(path)
        if not render_b64:
            return orig_folder, fn, {"error": "Failed to encode rendering image"}
            
        # We build a prompt with the candidate reference images
        parts = [
            {"text": "You are a quality control assistant. Below is an interior room rendering showing a specific piece of furniture:\n"},
            {"inlineData": {"mimeType": "image/jpeg", "data": render_b64}},
            {"text": "\nYour task is to identify which of the following reference products is visually shown in the rendering. Look very closely at the shape, design, color, materials, legs, drawers, doors, or armrests of the furniture items.\n\nHere are the candidate reference images:\n"}
        ]
        
        ref_mapping = {}
        for idx, cand in enumerate(candidates):
            ref_path = cand["ref_path"]
            if ref_path and os.path.exists(ref_path):
                ref_b64 = encode_image(ref_path)
                if ref_b64:
                    cand_key = f"ref_{idx+1}"
                    parts.append({"text": f"\nCandidate {cand_key} (SKU: {cand['sku']} | {cand['name']}):\n"})
                    parts.append({"inlineData": {"mimeType": "image/jpeg", "data": ref_b64}})
                    ref_mapping[cand_key] = cand
                    
        if not ref_mapping:
            # Fallback if no reference images exist/could be encoded
            # Let's map to the first candidate by default if no reference image is found
            first_cand = candidates[0]
            return orig_folder, fn, {
                "matched_sku": first_cand["sku"],
                "matched_name": first_cand["name"],
                "explanation": "Mapped to first candidate automatically (no reference images available for visual comparison)"
            }
            
        # prompt question
        parts.append({"text": "\nDetermine which single candidate reference product is visually shown in the rendering. Return your answer strictly as a JSON object with keys 'matched_sku', 'matched_name', and 'explanation'. If none of the reference images match the visual design or color of the furniture in the rendering, set 'matched_sku' to null.\n"})
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            res = requests.post(url, headers=headers, json=data, timeout=60)
            if res.status_code == 200:
                result_json = res.json()['candidates'][0]['content']['parts'][0]['text']
                decision = json.loads(result_json)
                return orig_folder, fn, decision
            return orig_folder, fn, {"error": f"API HTTP {res.status_code}"}
        except Exception as e:
            return orig_folder, fn, {"error": str(e)}

    # Run loop
    print("Starting Gemini visual cross-matching...")
    
    # Use ThreadPoolExecutor to run concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_render, item): item for item in renders_to_process}
        for future in as_completed(futures):
            item = futures[future]
            orig_folder, fn, res = future.result()
            
            if orig_folder not in redirection_plan:
                redirection_plan[orig_folder] = {}
                
            redirection_plan[orig_folder][fn] = res
            
            # Print feedback
            if "error" in res:
                print(f"  Processed {orig_folder}/{fn} -> ERROR: {res['error']}")
            else:
                print(f"  Processed {orig_folder}/{fn} -> Matched SKU: {res.get('matched_sku')} ({res.get('matched_name')})")
                
    # Save the redirection plan
    plan_path = os.path.join(PROJECT_DIR, "scratch", "furniture_redirection_plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(redirection_plan, f, indent=2, ensure_ascii=False)
        
    print(f"\nVisual cross-matching complete. Redirection plan saved to {plan_path}")

if __name__ == "__main__":
    main()
