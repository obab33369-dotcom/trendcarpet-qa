import os
import re
import requests
import json
import base64
import shutil
from io import BytesIO
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

SOURCE_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")
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

def download_image(url, dest_path):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            print(f"  [DOWNLOAD SUCCESS] Saved to {dest_path}")
            return True
        else:
            print(f"  [DOWNLOAD FAILED] Status code {response.status_code} for URL: {url}")
    except Exception as e:
        print(f"  [DOWNLOAD ERROR] {e} for URL: {url}")
    return False

def get_sku(folder_name):
    m = re.search(r'\(([^)]+)\)', folder_name)
    if m:
        return m.group(1).strip()
    return None

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

def verify_batch_with_gemini(ref_path, img_paths):
    if not API_KEY:
        return {}
        
    ref_b64 = encode_image(ref_path)
    if not ref_b64:
        return {}
        
    parts = [
        {"text": "You are a quality control assistant. Here is a REFERENCE image showing a specific carpet/rug product:\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": ref_b64}},
        {"text": "\nBelow are several CANDIDATE interior rendering images. For each candidate image, determine if the EXACT carpet/rug product shown in the REFERENCE image is present and looks correct (same pattern, design, color, shape, and key features). Note that there might be similar carpets in different shapes, colors, or patterns, which should be marked as FALSE. If the exact carpet/rug is present in the room rendering, answer TRUE, otherwise FALSE.\n\nReturn the results strictly as a JSON object mapping the index of each image to a boolean value. For example:\n{\n  \"image_1\": true,\n  \"image_2\": false\n}\n\nHere are the candidate images:\n"}
    ]
    
    encoded_images = {}
    valid_paths = []
    for idx, path in enumerate(img_paths):
        b64 = encode_image(path)
        if b64:
            img_key = f"image_{idx+1}"
            parts.append({"text": f"\nCandidate {img_key}:\n"})
            parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})
            encoded_images[img_key] = os.path.basename(path)
            valid_paths.append(path)
            
    if not valid_paths:
        return {}

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
            decisions = json.loads(result_json)
            
            output_decisions = {}
            for k, val in decisions.items():
                if k in encoded_images:
                    filename = encoded_images[k]
                    output_decisions[filename] = bool(val)
            return output_decisions
        return {}
    except Exception:
        return {}

def process_folder(folder_name):
    src_folder = os.path.join(SOURCE_DIR, folder_name)
    if not os.path.isdir(src_folder):
        return
        
    # Find reference image
    ref_image = None
    for f in os.listdir(src_folder):
        if f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png')):
            ref_image = os.path.join(src_folder, f)
            break
            
    if not ref_image:
        print(f"Skipping '{folder_name}' - still no reference image.")
        return
        
    # Collect candidate files
    candidates = []
    for f in os.listdir(src_folder):
        if f.startswith("00_REFERENCE_") or f == "reserv" or f == "discarded_by_gemini":
            continue
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            candidates.append(os.path.join(src_folder, f))
            
    # Also collect from reserv folder if exists
    reserv_folder = os.path.join(src_folder, "reserv")
    has_reserv = os.path.exists(reserv_folder)
    if has_reserv:
        for f in os.listdir(reserv_folder):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                candidates.append(os.path.join(reserv_folder, f))
                
    if not candidates:
        print(f"No candidates to process for '{folder_name}'.")
        return
        
    print(f"Running Gemini review on '{folder_name}' ({len(candidates)} candidates)...")
    
    # Process in batches of 15
    batch_size = 15
    all_decisions = {}
    
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        decisions = verify_batch_with_gemini(ref_image, batch)
        all_decisions.update(decisions)
        
    # Execute decisions
    discarded_count = 0
    kept_count = 0
    dest_discard_folder = os.path.join(DISCARD_DIR, folder_name)
    
    for path in candidates:
        fn = os.path.basename(path)
        is_keep = all_decisions.get(fn, True)
        in_reserv = "reserv" in os.path.dirname(path)
        
        if not is_keep:
            discarded_count += 1
            os.makedirs(dest_discard_folder, exist_ok=True)
            # Copy reference photo
            ref_fn = os.path.basename(ref_image)
            ref_dest = os.path.join(dest_discard_folder, ref_fn)
            if not os.path.exists(ref_dest):
                try:
                    shutil.copy2(ref_image, ref_dest)
                except Exception:
                    pass
            
            # Move file
            if in_reserv:
                discard_reserv = os.path.join(dest_discard_folder, "reserv")
                os.makedirs(discard_reserv, exist_ok=True)
                dest_path = os.path.join(discard_reserv, fn)
            else:
                dest_path = os.path.join(dest_discard_folder, fn)
                
            try:
                shutil.move(path, dest_path)
            except Exception:
                pass
        else:
            kept_count += 1
            
    print(f"Finished '{folder_name}': Kept {kept_count}, Discarded {discarded_count} images.")

def main():
    brand_dict_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
    sku_map_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'sku_map.json')
    
    with open(brand_dict_path, 'r', encoding='utf-8') as f:
        brand_dict = json.load(f)
        
    with open(sku_map_path, 'r', encoding='utf-8') as f:
        sku_map = json.load(f)

    # 1. Scan for folders missing reference image
    folders = [f for f in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, f))]
    missing_folders = []
    
    for folder in folders:
        folder_path = os.path.join(SOURCE_DIR, folder)
        has_ref = False
        for f in os.listdir(folder_path):
            if f.startswith("00_REFERENCE_"):
                has_ref = True
                break
        if not has_ref:
            missing_folders.append(folder)
            
    if not missing_folders:
        print("All folders have reference images. No missing references found.")
        return
        
    print(f"Found {len(missing_folders)} folders missing reference images:")
    for f in missing_folders:
        print(f"  - {f}")
        
    # 2. Download missing references
    downloaded_folders = []
    for folder in missing_folders:
        sku = get_sku(folder)
        if not sku:
            print(f"  Cannot extract SKU from folder name: {folder}")
            continue
            
        dest_path = os.path.join(SOURCE_DIR, folder, f"00_REFERENCE_{sku}.jpg")
        print(f"\nProcessing SKU: {sku} in folder '{folder}'...")
        
        # Search brand_dict
        image_path = None
        for slug, info in brand_dict.items():
            if info.get('sku') == sku:
                image_path = info.get('image_path')
                break
                
        # Search sku_map
        if not image_path:
            for k, info in sku_map.items():
                if info.get('sku') == sku:
                    curr_imgs = info.get('current_images', [])
                    if curr_imgs:
                        image_path = curr_imgs[0]
                        break
                        
        download_success = False
        if image_path:
            if image_path.startswith("http"):
                url = image_path
            else:
                if not image_path.startswith("/"):
                    image_path = "/" + image_path
                url = f"https://www.reformasthlm.se{image_path}"
            print(f"  Found image path: {image_path}. Downloading: {url}...")
            download_success = download_image(url, dest_path)
        else:
            guess_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}.jpg"
            print(f"  SKU not found in DB. Trying guess: {guess_url}...")
            download_success = download_image(guess_url, dest_path)
            if not download_success:
                guess_url_png = f"https://www.reformasthlm.se/bilder/artiklar/{sku}.png"
                print(f"  Trying guess: {guess_url_png}...")
                download_success = download_image(guess_url_png, dest_path)
                
        if download_success:
            downloaded_folders.append(folder)
            
    # 3. Run Gemini cleanup specifically on these folders
    if downloaded_folders:
        print("\n=== Running Gemini cleanup on newly resolved folders ===")
        for folder in downloaded_folders:
            try:
                process_folder(folder)
            except Exception as e:
                print(f"Error processing folder '{folder}': {e}")
    else:
        print("\nNo references were successfully downloaded. Skipping Gemini cleanup.")

if __name__ == "__main__":
    main()
