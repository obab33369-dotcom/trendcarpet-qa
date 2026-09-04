import os
import json
import base64
import requests
import re
import shutil
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")
GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

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
    except Exception as e:
        return None

def classify_rendering(render_path, catalog):
    if not API_KEY:
        return {"error": "No API Key"}
        
    render_b64 = encode_image(render_path)
    if not render_b64:
        return {"error": "Failed to encode image"}
        
    # Group catalog options by family for better readability in the prompt
    families = {}
    for sku, info in catalog.items():
        fn = info['folder_name']
        family_name = fn.split(' - ')[0].replace("Matta ", "").replace("Ryamatta ", "")
        if family_name not in families:
            families[family_name] = []
        families[family_name].append(f"- SKU: {sku} | {fn}")
        
    catalog_text = ""
    for fam, items in sorted(families.items()):
        catalog_text += f"\n### Family: {fam}\n"
        catalog_text += "\n".join(items) + "\n"

    parts = [
        {"text": "You are a quality control assistant. Below is an interior room rendering showing a specific carpet/rug in the center of the room:\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": render_b64}},
        {"text": f"\nYour task is to identify which carpet product and SKU from our catalog is visually shown in the rendering. Look very closely at the carpet's design pattern, shape, edge style (e.g. straight vs. wavy/scalloped border), and colors.\n\nHere is our catalog of carpet options grouped by design family:\n{catalog_text}\n\nDetermine the single best matching product SKU. Note that design families have very distinct visual features:\n- Arvella: abstract organic/watercolor shapes in multi-color, brun, or brun/svart.\n- Aureline: plain color in center, with a very distinct wavy/scalloped darker border.\n- Avendo: repeating 3D geometric block/isometric stepped cube patterns.\n- Belden: abstract design with round circles and curved bands.\n- Calvera: minimalist repeating diamond patterns.\n- Carrano: classic checkboard pattern with alternating squares.\n- Sorvento: complex geometric grid/tiled squares.\n- Ventaro: abstract design with organic flowing curved shapes.\n- Ängelholm: solid/plain textured rug.\n- Velenna: concentric pattern or red/beige organic shapes.\n- Orlisse/Oralia/etc.\n\nReturn your answer strictly as a JSON object with keys 'matched_sku', 'matched_name', and 'explanation'. If no option in the catalog matches the visual design or colors of the carpet in the rendering, set 'matched_sku' to null.\n"}
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
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=60)
        if res.status_code == 200:
            result_json = res.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(result_json)
        return {"error": f"API status code {res.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    # Load catalog
    catalog_path = os.path.join(PROJECT_DIR, "scratch", "carpet_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    # 18 flagged folders with 0 kept images
    flagged_folders = [
        "Matta Aravelle - Multi (RG01-20)",
        "Matta Aureline - BeigeBrun (RG01-8)",
        "Matta Aureline - Grön (RG01-9)",
        "Matta Aureline BeigeGrå (RG01-7)",
        "Matta Avendo - GulBeige (RG01-76)",
        "Matta Avendo - Röd (RG01-75)",
        "Matta Belden - Grön (RG01-74)",
        "Matta Belden - Röd (RG01-73)",
        "Matta Calvera - Grå (RG01-35)",
        "Matta Calvera - Röd (RG01-34)",
        "Matta Carrano - GråVit (RG01-72)",
        "Matta Carrano - Grön (RG01-71)",
        "Matta Carrano - SvartVit (RG01-70)",
        "Matta Ventaro - GrönGul (RG01-91)",
        "Matta Ventaro - RosaBrun (RG01-90)",
        "Matta Ängelholm - GråBlå (RG002)",
        "Matta Ängelholm - Grön (RG00)",
        "Matta Ängelholm - Mörkbrun (RG001)"
    ]
    
    # Collect all rendering files currently in the discard folder for these flagged carpet products
    mismatches = []
    for folder in flagged_folders:
        discard_path = os.path.join(DISCARD_ROOT, folder)
        if not os.path.exists(discard_path):
            continue
        for f in os.listdir(discard_path):
            if not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                mismatches.append((folder, f, os.path.join(discard_path, f)))
                
    print(f"Found {len(mismatches)} discarded rendering files to visually cross-match.")
    
    results = {}
    
    def process_item(item):
        orig_folder, fn, path = item
        res = classify_rendering(path, catalog)
        return orig_folder, fn, path, res
        
    print("Running Gemini visual classification...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_item, item): item for item in mismatches}
        for future in as_completed(futures):
            orig_folder, fn, path, res = future.result()
            if orig_folder not in results:
                results[orig_folder] = {}
            results[orig_folder][fn] = res
            print(f"  Processed {orig_folder}/{fn} -> Matched: {res.get('matched_sku')} ({res.get('matched_name')})")
            
    # Save the redirection plan
    plan_path = os.path.join(PROJECT_DIR, "scratch", "carpet_redirection_plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\nVisual cross-matching complete. Redirection plan saved to {plan_path}")

if __name__ == "__main__":
    main()
