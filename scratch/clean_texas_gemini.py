import os
import sys
import re
import json
import time
import base64
import shutil
from io import BytesIO
from PIL import Image
import requests

# Reconfigure stdout/stderr to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
TARGET_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering\Baddsoffa Texas Ljusgra (MLM-502580-lightgrey)"
DISCARDED_DIR = os.path.join(TARGET_DIR, "discarded_by_gemini")

os.makedirs(DISCARDED_DIR, exist_ok=True)

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

GEMINI_API_KEY = load_gemini_key()
if not GEMINI_API_KEY:
    print("Error: Gemini API key not found!")
    sys.exit(1)

def encode_image(img_path, max_size=600):
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((max_size, max_size))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image {img_path}: {e}")
        return None

def query_gemini_comparison(ref_base64, cand_base64, max_retries=5):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt = """You are a quality control assistant for a furniture retailer.
You are given two images:
1. The FIRST image is the Reference Image showing a specific piece of furniture.
2. The SECOND image is the Interior Scene Image where that exact piece of furniture is supposed to be placed.

Your task is to analyze both images and determine if the EXACT piece of furniture shown in the Reference Image is present in the Interior Scene Image.

Guidelines:
- Look for identical design, shape, materials, colors, cushions, legs, arms, and structural details.
- If the Interior Scene contains a similar but different model (e.g. different legs, different shape, different number of cushions, different armrests, or entirely different style), classify it as NOT present (present = false).
- The furniture might be seen from a different angle, partially hidden behind a table or pillow, or in different lighting. Use your visual reasoning to determine if it is indeed the exact same model.
- If it is present, set "present" to true.
- If it is not present, set "present" to false.

You must respond with a JSON object in this exact format:
{
  "present": true or false,
  "confidence": a float between 0.0 and 1.0,
  "reason": "a brief reason in Swedish explaining why you decided it is present or not, pointing out matching or mismatching details"
}
"""

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": ref_base64}},
                    {"inlineData": {"mimeType": "image/jpeg", "data": cand_base64}}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                resp_json = res.json()
                text = resp_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(text.strip())
            elif res.status_code == 429:
                backoff = 5 * (attempt + 1)
                print(f"Rate limit hit (429), waiting {backoff} seconds...")
                time.sleep(backoff)
            else:
                print(f"API Error {res.status_code}: {res.text}")
                time.sleep(2)
        except Exception as e:
            print(f"Attempt {attempt+1} failed with error: {e}")
            time.sleep(2)
            
    return {"present": True, "reason": "Error calling Gemini API after retries", "confidence": 0.0}

def main():
    # Find reference image
    ref_path = None
    for f in os.listdir(TARGET_DIR):
        if "reference" in f.lower() and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            ref_path = os.path.join(TARGET_DIR, f)
            break
            
    if not ref_path:
        print("Error: Reference image not found in target directory.")
        sys.exit(1)
        
    print(f"Using reference image: {ref_path}")
    ref_base64 = encode_image(ref_path)
    if not ref_base64:
        print("Error encoding reference image.")
        sys.exit(1)
        
    # Scan all candidate images in TARGET_DIR and TARGET_DIR/reserv
    candidates = []
    
    # 1. Main folder candidates
    for f in os.listdir(TARGET_DIR):
        f_path = os.path.join(TARGET_DIR, f)
        if os.path.isdir(f_path):
            continue
        if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
        if "reference" in f.lower():
            continue
        candidates.append((f_path, TARGET_DIR))
        
    # 2. Reserv folder candidates
    reserv_dir = os.path.join(TARGET_DIR, "reserv")
    if os.path.exists(reserv_dir):
        for f in os.listdir(reserv_dir):
            f_path = os.path.join(reserv_dir, f)
            if os.path.isdir(f_path):
                continue
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            candidates.append((f_path, reserv_dir))

    print(f"Found {len(candidates)} candidates to analyze.")
    
    total_kept = 0
    total_discarded = 0
    
    for c_path, orig_folder in candidates:
        fn = os.path.basename(c_path)
        is_in_reserv = (os.path.basename(orig_folder) == "reserv")
        label = "reserv" if is_in_reserv else "primary"
        print(f"Analyzing [{label}] {fn}...", end=" ", flush=True)
        
        cand_base64 = encode_image(c_path)
        if not cand_base64:
            print("Encoding Error")
            continue
            
        result = query_gemini_comparison(ref_base64, cand_base64)
        is_present = result.get("present", True)
        reason = result.get("reason", "")
        confidence = result.get("confidence", 0.0)
        
        if is_present:
            print(f"KEEP (Confidence: {confidence:.2f})")
            print(f"  Reason: {reason}")
            total_kept += 1
        else:
            print(f"DISCARD (Confidence: {confidence:.2f})")
            print(f"  Reason: {reason}")
            total_discarded += 1
            # Move to discarded directory
            dest_path = os.path.join(DISCARDED_DIR, fn)
            try:
                shutil.move(c_path, dest_path)
            except Exception as e:
                print(f"  Error moving file: {e}")
                
        time.sleep(1.0)
        
    print("\n" + "=" * 50)
    print("TEXAS SOFA VERIFICATION COMPLETED")
    print("=" * 50)
    print(f"Total Kept:      {total_kept}")
    print(f"Total Discarded: {total_discarded}")
    print("=" * 50)

if __name__ == "__main__":
    main()
