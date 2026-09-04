import os
import json
import base64
import requests
import shutil
from io import BytesIO
from PIL import Image

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

REF_SRC = os.path.join(WORKSPACE_DIR, "reforma-original-images", "102612.jpg")
NEW_VADDO_FOLDER = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering", "Barstol Vaddo Beige (102612)")
OLD_VESTBY_DISCARD = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering-borttagna", "Barstol Vestby - Beigebrun (2010001196273)")
NEW_VADDO_DISCARD = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering-borttagna", "Barstol Vaddo Beige (102612)")

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
        print("Gemini API key not found!")
        return {}
        
    ref_b64 = encode_image(ref_path)
    if not ref_b64:
        print("Failed to encode reference image.")
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
            print(f"Gemini API returned error code {res.status_code}: {res.text}")
        return {}
    except Exception as e:
        print(f"Exception during Gemini API request: {e}")
        return {}

def main():
    print("=== STARTING SELECTIVE FIX FOR VADDO BEIGE ===")
    
    # 1. Create target folder and copy reference image
    if not os.path.exists(REF_SRC):
        print(f"Error: Reference source image {REF_SRC} not found!")
        return
        
    print(f"Creating new folder: {NEW_VADDO_FOLDER}")
    os.makedirs(NEW_VADDO_FOLDER, exist_ok=True)
    
    ref_dest = os.path.join(NEW_VADDO_FOLDER, "00_REFERENCE_102612.jpg")
    print(f"Copying reference image to {ref_dest}")
    shutil.copy2(REF_SRC, ref_dest)
    
    # 2. Identify and move the files from old Vestby discard folder
    if not os.path.exists(OLD_VESTBY_DISCARD):
        print(f"Error: Old Vestby discard folder {OLD_VESTBY_DISCARD} not found!")
        return
        
    moved_files = []
    files_to_move = [
        "075-architectural-digest-style-075.png",
        "075-architectural-digest-style-075b.png",
        "076-architectural-digest-style-076.png"
    ]
    
    for fn in files_to_move:
        src_file = os.path.join(OLD_VESTBY_DISCARD, fn)
        if os.path.exists(src_file):
            dest_file = os.path.join(NEW_VADDO_FOLDER, fn)
            print(f"Moving {fn} from old Vestby discard to new Vaddo folder...")
            shutil.move(src_file, dest_file)
            moved_files.append(dest_file)
        else:
            print(f"Warning: File {fn} not found in old Vestby discard folder.")
            
    # 3. Clean up the old Vestby discard folder
    # List remaining files
    remaining = os.listdir(OLD_VESTBY_DISCARD)
    # Filter out reference image or thumbs
    remaining_actual = [f for f in remaining if f != "00_REFERENCE_2010001196273.jpg" and f != "desktop.ini"]
    if not remaining_actual:
        print(f"Old Vestby discard folder is now empty of renders. Deleting it: {OLD_VESTBY_DISCARD}")
        try:
            shutil.rmtree(OLD_VESTBY_DISCARD)
        except Exception as e:
            print(f"Error deleting old Vestby discard folder: {e}")
    else:
        print(f"Old Vestby discard folder still contains other files: {remaining_actual}")
        
    # 4. Call Gemini to visually verify the moved files in the new folder
    if not moved_files:
        print("No files were moved to evaluate.")
        return
        
    print("\nCalling Gemini API to verify the moved images against the Väddö Beige reference...")
    decisions = verify_batch_with_gemini(ref_dest, moved_files)
    print(f"Gemini Decisions: {decisions}")
    
    # 5. Execute Gemini decisions
    discarded_count = 0
    kept_count = 0
    
    for path in moved_files:
        fn = os.path.basename(path)
        is_keep = decisions.get(fn, True) # Default to true if API failed
        
        if not is_keep:
            discarded_count += 1
            print(f"  Gemini REJECTED '{fn}'. Moving to new Vaddo discard folder...")
            os.makedirs(NEW_VADDO_DISCARD, exist_ok=True)
            
            # Copy reference photo to new discard folder
            ref_discard_dest = os.path.join(NEW_VADDO_DISCARD, "00_REFERENCE_102612.jpg")
            if not os.path.exists(ref_discard_dest):
                shutil.copy2(ref_dest, ref_discard_dest)
                
            dest_path = os.path.join(NEW_VADDO_DISCARD, fn)
            shutil.move(path, dest_path)
        else:
            kept_count += 1
            print(f"  Gemini ACCEPTED '{fn}'. Keeping in clean folder.")
            
    print(f"\nVerification finished: Kept {kept_count}, Discarded {discarded_count} images.")

if __name__ == "__main__":
    main()
