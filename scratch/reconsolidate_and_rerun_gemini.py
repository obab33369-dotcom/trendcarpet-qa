import os
import shutil
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        print(f"Skipping '{folder_name}' - no reference image.")
        return
        
    # Collect candidate files
    candidates = []
    for f in os.listdir(src_folder):
        if f.startswith("00_REFERENCE_") or f == "reserv" or f == "discarded_by_gemini":
            continue
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            candidates.append(os.path.join(src_folder, f))
            
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
            dest_path = os.path.join(dest_discard_folder, fn)
            try:
                shutil.move(path, dest_path)
            except Exception:
                pass
        else:
            kept_count += 1
            
    print(f"Finished '{folder_name}': Kept {kept_count}, Discarded {discarded_count} images.")

def main():
    # 21 flagged folders
    flagged_folders = [
        "Matta Aravelle - Multi (RG01-20)",
        "Matta Arvella - RödGrön (RG01-65)",
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
        "Matta Ventaro - Multi (RG01-87)",
        "Matta Ventaro - RosaBrun (RG01-90)",
        "Matta Ängelholm - GråBlå (RG002)",
        "Matta Ängelholm - Grön (RG00)",
        "Matta Ängelholm - Mörkbrun (RG001)",
        "Ryamatta Aranga Super Soft Fur Rosa (H100017)"
    ]
    
    print("=== RECONSOLIDATING FLAGGED FOLDERS ===")
    
    recon_count = 0
    for folder in flagged_folders:
        src_path = os.path.join(DISCARD_DIR, folder)
        dest_path = os.path.join(SOURCE_DIR, folder)
        
        if not os.path.exists(src_path):
            continue
            
        # Move all candidate files back to clean folder
        files_to_move = [f for f in os.listdir(src_path) if not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if files_to_move:
            os.makedirs(dest_path, exist_ok=True)
            for f in files_to_move:
                shutil.move(os.path.join(src_path, f), os.path.join(dest_path, f))
            recon_count += len(files_to_move)
            print(f"  Moved {len(files_to_move)} renders back to clean: {folder}")
            
        # Delete empty discard folder
        try:
            # Remove reference image first
            for f in os.listdir(src_path):
                if f.startswith("00_REFERENCE_"):
                    os.remove(os.path.join(src_path, f))
            if not os.listdir(src_path):
                os.rmdir(src_path)
        except Exception:
            pass
            
    print(f"Reconsolidated total of {recon_count} rendering files.")
    
    print("\n=== RUNNING GEMINI CLEANUP ON RECONSOLIDATED FOLDERS ===")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_folder, f): f for f in flagged_folders}
        for future in as_completed(futures):
            folder = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing folder '{folder}': {e}")
                
    print("\n=== RE-EVALUATION COMPLETE ===")

if __name__ == "__main__":
    main()
