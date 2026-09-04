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

# Reconfigure stdout/stderr to UTF-8 to prevent encoding crashes on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
LOCAL_REFORMA_ORIG = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-original-images"
SKU_MAP_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\sku_map.json"
ONEDRIVE_PICTURES = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
INTERIORS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-26-06"
DISCARDED_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\from Reforma interiörer 26-06-discarded"
GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

# Load Gemini API Key
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

# Load SKU map for reverse filename lookups
sku_to_filename = {}
if os.path.exists(SKU_MAP_PATH):
    try:
        with open(SKU_MAP_PATH, 'r', encoding='utf-8') as f:
            sku_map = json.load(f)
            for filename, info in sku_map.items():
                sku = info.get('sku')
                if sku:
                    sku_to_filename[sku] = filename
    except Exception as e:
        print(f"Warning: Could not load SKU map from {SKU_MAP_PATH}: {e}")

# Helper to extract SKU from folder name
def get_sku_from_dir_name(dir_name):
    match = re.search(r'\(([^)]+)\)$', dir_name)
    if match:
        return match.group(1).strip()
    return None

# Resolve reference image path for a directory
def find_reference_image(dir_path, dir_name):
    # 1. Look in local folder for *REFERENCE*
    for f in os.listdir(dir_path):
        if 'reference' in f.lower() and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return os.path.join(dir_path, f), "local_folder_reference"
            
    sku = get_sku_from_dir_name(dir_name)
    if not sku:
        return None, "no_sku"
        
    # 2. Look in local reforma-original-images
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        local_path = os.path.join(LOCAL_REFORMA_ORIG, f"{sku}{ext}")
        if os.path.exists(local_path):
            return local_path, "local_reforma_original"
            
    # 3. Check mapped filename from SKU map
    mapped_filename = sku_to_filename.get(sku)
    
    # 4. Look in OneDrive product directories
    product_search_dirs = [
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter"),
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter_aktiva"),
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter_aktiva_del1"),
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter_aktiva_del2"),
    ]
    # Add batch 1 folders
    for i in range(1, 9):
        product_search_dirs.append(os.path.join(ONEDRIVE_PICTURES, f"turboflow_batch1_produkter_aktiva_del{i}"))
        
    for p_dir in product_search_dirs:
        if not os.path.exists(p_dir):
            continue
            
        # Try mapped filename first
        if mapped_filename:
            base_mapped, _ = os.path.splitext(mapped_filename)
            for f in os.listdir(p_dir):
                base_f, _ = os.path.splitext(f)
                if base_mapped.lower() == base_f.lower():
                    return os.path.join(p_dir, f), f"onedrive_mapped_{os.path.basename(p_dir)}"
        
        # Try generic search for SKU in filenames
        for f in os.listdir(p_dir):
            if sku in f and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return os.path.join(p_dir, f), f"onedrive_sku_{os.path.basename(p_dir)}"
                
    return None, "not_found"

# Scale and encode image as base64 JPEG
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

# Call Gemini multimodal model to check if the product matches the interior
def query_gemini_comparison(ref_base64, cand_base64, max_retries=5):
    if not GEMINI_API_KEY:
        return {"present": True, "reason": "No API key loaded", "confidence": 0.0}
        
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
                result = json.loads(text.strip())
                return result
            elif res.status_code == 429:
                backoff = 5 * (attempt + 1)
                print(f"    Rate limit hit (429), waiting {backoff} seconds...")
                time.sleep(backoff)
            else:
                print(f"    API Error {res.status_code}: {res.text}")
                time.sleep(2)
        except Exception as e:
            print(f"    Attempt {attempt+1} failed with error: {e}")
            time.sleep(2)
            
    return {"present": True, "reason": "Error calling Gemini API after retries", "confidence": 0.0}

def process_interiors():
    if not GEMINI_API_KEY:
        print("[ERROR] Gemini API key not found! Please check GEMINI_API_KEY.env.")
        return
        
    print("=" * 60)
    print("REFORMA INTERIORS CLEANUP VIA GEMINI API")
    print("=" * 60)
    
    # 1. Scan subdirectories
    if not os.path.exists(INTERIORS_DIR):
        print(f"[ERROR] Target directory does not exist: {INTERIORS_DIR}")
        return
        
    subdirs = sorted([d for d in os.listdir(INTERIORS_DIR) if os.path.isdir(os.path.join(INTERIORS_DIR, d))])
    print(f"Found {len(subdirs)} subdirectories in total.")
    
    # Menu selections
    print("\nSelect mode:")
    print("  1. Status check (Verify reference images and count candidates)")
    print("  2. Dry Run (Run Gemini comparison, but do not move/delete files)")
    print("  3. Sharp Run (Run Gemini comparison, move non-matching images to discarded folder)")
    
    mode_input = input("Enter choice (1-3): ").strip()
    if mode_input == '1':
        mode = 'status'
    elif mode_input == '2':
        mode = 'dry'
    elif mode_input == '3':
        mode = 'sharp'
    else:
        print("Invalid choice, defaulting to Status Check.")
        mode = 'status'
        
    folder_filter = input("\nFilter folders by name prefix/substring (leave empty for all folders): ").strip()
    
    limit_folders_input = input("Limit number of folders to process (leave empty for unlimited): ").strip()
    limit_folders = int(limit_folders_input) if limit_folders_input.isdigit() else None
    
    limit_images_input = input("Limit total images to analyze (leave empty for unlimited): ").strip()
    limit_images = int(limit_images_input) if limit_images_input.isdigit() else None
    
    start_folder_input = input("Start from folder index (1-205, default 1): ").strip()
    start_folder_idx = int(start_folder_input) if start_folder_input.isdigit() else 1
    
    # Filter folders
    target_folders = []
    for sd in subdirs:
        if folder_filter and folder_filter.lower() not in sd.lower():
            continue
        target_folders.append(sd)
        
    total_folders_count = len(target_folders)
    
    # Slice to start from the selected index
    if start_folder_idx > 1:
        target_folders = target_folders[start_folder_idx - 1:]
        
    if limit_folders:
        target_folders = target_folders[:limit_folders]
        
    print(f"\nWill process {len(target_folders)} folders (starting from index {start_folder_idx}) in mode '{mode.upper()}'.\n")
    
    total_analyzed = 0
    total_approved = 0
    total_removed = 0
    total_errors = 0
    
    for i, sd in enumerate(target_folders):
        current_abs_idx = start_folder_idx + i
        dir_path = os.path.join(INTERIORS_DIR, sd)
        print(f"\n[{current_abs_idx}/{total_folders_count}] Folder: {sd}")
        
        # Resolve reference
        ref_path, ref_source = find_reference_image(dir_path, sd)
        if not ref_path:
            print(f"  Warning: Reference image NOT found (Source/Reason: {ref_source}). Skipping folder.")
            continue
            
        print(f"  Reference image: {os.path.basename(ref_path)} ({ref_source})")
        
        # Scan candidate images
        candidates = []
        for f in os.listdir(dir_path):
            file_path = os.path.join(dir_path, f)
            if os.path.isdir(file_path):
                continue
            if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
            if f.startswith('_temp_'):
                continue
            # Skip reference image
            if os.path.abspath(file_path) == os.path.abspath(ref_path):
                continue
            candidates.append(f)
            
        print(f"  Found {len(candidates)} candidate interior images.")
        
        if mode == 'status':
            continue
            
        if not candidates:
            continue
            
        # Encode reference image
        ref_base64 = encode_image(ref_path)
        if not ref_base64:
            print("  Error encoding reference image, skipping folder.")
            continue
            
        # Analyze each candidate
        for c_file in candidates:
            if limit_images and total_analyzed >= limit_images:
                print("\nReached maximum image limit. Stopping.")
                break
                
            c_path = os.path.join(dir_path, c_file)
            print(f"  - Analyzing image: {c_file}...", end=" ", flush=True)
            
            cand_base64 = encode_image(c_path)
            if not cand_base64:
                print("Encoding Error")
                total_errors += 1
                continue
                
            # Query Gemini
            result = query_gemini_comparison(ref_base64, cand_base64)
            total_analyzed += 1
            
            is_present = result.get("present", True)
            reason = result.get("reason", "No reason provided")
            confidence = result.get("confidence", 0.0)
            
            if is_present:
                print(f"MATCH (Confidence: {confidence:.2f})")
                print(f"    Reason: {reason}")
                total_approved += 1
            else:
                print(f"NO MATCH (Confidence: {confidence:.2f})")
                print(f"    Reason: {reason}")
                total_removed += 1
                
                # Perform move if sharp mode
                if mode == 'sharp':
                    product_discard_dir = os.path.join(DISCARDED_DIR, sd)
                    os.makedirs(product_discard_dir, exist_ok=True)
                    
                    # Copy reference image if not already there
                    dest_ref_path = os.path.join(product_discard_dir, os.path.basename(ref_path))
                    if not os.path.exists(dest_ref_path):
                        try:
                            shutil.copy2(ref_path, dest_ref_path)
                        except Exception as e_copy:
                            print(f"    [Warning: Could not copy reference image: {e_copy}]")
                            
                    dest_path = os.path.join(product_discard_dir, c_file)
                    
                    try:
                        # If destination already exists, append timestamp
                        if os.path.exists(dest_path):
                            base, ext = os.path.splitext(c_file)
                            dest_path = os.path.join(product_discard_dir, f"{base}_{int(time.time())}{ext}")
                        os.rename(c_path, dest_path)
                        print(f"    [MOVED to from Reforma interiörer 26-06-discarded]")
                    except Exception as e:
                        print(f"    [ERROR moving file: {e}]")
                        total_errors += 1
                else:
                    print(f"    [DRY-RUN: Would move to from Reforma interiörer 26-06-discarded]")
                    
            # Rate limit backoff
            time.sleep(1.0)
            
        if limit_images and total_analyzed >= limit_images:
            break
            
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Mode:             {mode.upper()}")
    print(f"Total analyzed:   {total_analyzed}")
    print(f"Approved (kept):  {total_approved}")
    print(f"Rejected:         {total_removed}")
    print(f"Errors/Skipped:   {total_errors}")
    if mode == 'sharp':
        print(f"Note: Rejected files have been safely moved to: {DISCARDED_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    process_interiors()
