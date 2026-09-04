import os
import re
import json
import base64
import requests
import shutil
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
SOURCE_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering-borttagna")

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
        print(f"Error encoding {img_path}: {e}")
        return None

def verify_batch_with_gemini(ref_path, img_paths):
    if not API_KEY:
        print("Error: Gemini API Key not found.")
        return {}
        
    ref_b64 = encode_image(ref_path)
    if not ref_b64:
        return {}
        
    parts = [
        {"text": "You are a quality control assistant. Here is a REFERENCE image showing a specific furniture product:\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": ref_b64}},
        {"text": "\nBelow are several CANDIDATE interior rendering images. For each candidate image, determine if the EXACT furniture product shown in the REFERENCE image is present and looks correct (same design, shape, and key features). Note that there might be similar products in different shapes/colors, which should be marked as FALSE. If the exact product is present, answer TRUE, otherwise FALSE.\n\nReturn the results strictly as a JSON object mapping the index of each image to a boolean value. For example:\n{\n  \"image_1\": true,\n  \"image_2\": false\n}\n\nHere are the candidate images:\n"}
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
        else:
            print(f"Gemini API Error: {res.status_code} - {res.text}")
            return {}
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return {}

def process_folder(folder_name, dry_run=True):
    src_folder = os.path.join(SOURCE_DIR, folder_name)
    if not os.path.isdir(src_folder):
        print(f"Folder {folder_name} not found.")
        return
        
    # Find reference image
    ref_image = None
    for f in os.listdir(src_folder):
        if f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png')):
            ref_image = os.path.join(src_folder, f)
            break
            
    if not ref_image:
        print(f"No reference image found in {folder_name}")
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
    if os.path.exists(reserv_folder):
        for f in os.listdir(reserv_folder):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                candidates.append(os.path.join(reserv_folder, f))
                
    if not candidates:
        print(f"No candidate images found in {folder_name}")
        return
        
    print(f"\nProcessing folder '{folder_name}' with {len(candidates)} candidates...")
    
    # Process in batches of 15
    batch_size = 15
    all_decisions = {}
    
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        print(f"  Verifying batch {i//batch_size + 1} ({len(batch)} images)...")
        decisions = verify_batch_with_gemini(ref_image, batch)
        all_decisions.update(decisions)
        
    # Execute decisions
    discarded_count = 0
    kept_count = 0
    
    dest_discard_folder = os.path.join(DISCARD_DIR, folder_name)
    
    for path in candidates:
        fn = os.path.basename(path)
        is_keep = all_decisions.get(fn, True) # Default to keep if API fails
        
        if not is_keep:
            discarded_count += 1
            if not dry_run:
                os.makedirs(dest_discard_folder, exist_ok=True)
                # Copy reference photo to discard folder if not already there
                ref_fn = os.path.basename(ref_image)
                ref_dest = os.path.join(dest_discard_folder, ref_fn)
                if not os.path.exists(ref_dest):
                    shutil.copy2(ref_image, ref_dest)
                
                # Move candidate file to discard folder
                dest_path = os.path.join(dest_discard_folder, fn)
                shutil.move(path, dest_path)
                print(f"  [DISCARDED] Moved {fn} to {os.path.basename(DISCARD_DIR)}")
        else:
            kept_count += 1
            
    print(f"Finished '{folder_name}': Kept {kept_count} images, Discarded {discarded_count} images.")

if __name__ == "__main__":
    # Test on the Texas Sofa Ljusgra folder
    # We set dry_run=False so it actually moves them
    process_folder("Baddsoffa Texas Ljusgra (MLM-502580-lightgrey)", dry_run=False)
