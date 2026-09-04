import os
import sys
import re
import json
import base64
import requests
import numpy as np
from PIL import Image
from io import BytesIO

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Paths
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full")
ARTIKLAR_DIR = os.path.join(FTP_UPLOAD_DIR, "artiklar")
GEMINI_ENV_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

def load_gemini_key():
    if os.path.exists(GEMINI_ENV_PATH):
        with open(GEMINI_ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

def create_grid_image(image_paths, cols=5, tile_size=500):
    n = len(image_paths)
    rows = (n + cols - 1) // cols
    grid_w = cols * tile_size
    grid_h = rows * tile_size
    
    # White background grid canvas
    grid_img = Image.new("RGB", (grid_w, grid_h), (255, 255, 255))
    
    for idx, path in enumerate(image_paths):
        r = idx // cols
        c = idx % cols
        try:
            with Image.open(path) as img:
                img_res = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                grid_img.paste(img_res, (c * tile_size, r * tile_size))
        except Exception as e:
            print(f"Error loading {path} for grid: {e}")
            
    return grid_img

def audit_grid_via_gemini(grid_pil, image_filenames, key):
    buffered = BytesIO()
    grid_pil.save(buffered, format="JPEG", quality=85)
    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "You are a quality control director for a premium e-commerce furniture brand (like Zara Home). "
        "Analyze this catalog grid of processed product shots. The images are ordered left-to-right, top-to-bottom. "
        f"The filenames corresponding to each position in the grid are: {', '.join(image_filenames)}.\n\n"
        "Note on Image Types:\n"
        "- Some images are 'lifestyle' or 'in-situ' shots (furniture in a real room). Ignore them for white-background/floor-line/clipping rules, as they are copied untouched by design.\n"
        "- Some images are close-up detail/zoom shots (e.g. focusing closely on wood texture, fabric, a single leg, a handle, or a technical drawing). Ignore them for floor-line/horizontal alignment/clipping rules, as they are meant to highlight a detail and are cropped closely by design.\n\n"
        "For the standard full-view 'studio' or 'cutout' shots (which show the entire product on a white background), please evaluate if:\n"
        "1. All products stand on the exact same virtual floor line (horizontal alignment is matching across images).\n"
        "2. All products are perfectly centered horizontally.\n"
        "3. There are no cut-off components, weird clippings, or floaters (the complete item is visible).\n"
        "4. The background is pure white (#FFFFFF).\n"
        "5. The overall look is completely professional (no off-center margins or awkward sizing).\n\n"
        "Reply strictly in JSON format:\n"
        "{\n"
        "  \"status\": \"pass\" | \"fail\",\n"
        "  \"failed_items\": [\n"
        "    {\n"
        "      \"filename\": \"string\",\n"
        "      \"defect\": \"description of centering, alignment, crop, or shadow error\"\n"
        "    }\n"
        "  ],\n"
        "  \"feedback\": \"Overall recommendations for correction\"\n"
        "}"
    )
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    res = requests.post(url, headers=headers, json=data, timeout=40)
    if res.status_code == 200:
        res_json = res.json()
        text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        return json.loads(text_resp)
    else:
        raise Exception(f"Gemini API request failed with status code {res.status_code}: {res.text}")

def main():
    print("==================================================")
    print("       GEMINI BATCH VISUAL AUDITING TOOL          ")
    print("==================================================")
    
    gemini_key = load_gemini_key()
    if not gemini_key:
        print("[ERROR] GEMINI_API_KEY.env not found. Cannot run auditing.")
        sys.exit(1)
        
    zoom_dir = os.path.join(ARTIKLAR_DIR, "zoom")
    if not os.path.exists(zoom_dir):
        print(f"[ERROR] Processed zoom folder does not exist: {zoom_dir}")
        sys.exit(1)
        
    test_skus = ["1200180", "T8044-white", "97828", "1311-L-S", "LINK-SM11-light"]
    
    # Gather all processed images in zoom folder
    all_files = os.listdir(zoom_dir)
    sku_to_files = {sku: [] for sku in test_skus}
    
    for filename in all_files:
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        # Find which SKU this file belongs to
        for sku in test_skus:
            # Match exactly the SKU prefix (e.g., "1200180_")
            if filename.startswith(sku + "_"):
                sku_to_files[sku].append(filename)
                break
                
    # Sort files for each SKU by slot number
    for sku in test_skus:
        sku_to_files[sku].sort(key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x)])
        
    os.makedirs("scratch", exist_ok=True)
    audit_report = {}
    
    sku_idx = 1
    for sku, files in sku_to_files.items():
        if not files:
            print(f"\n[WARNING] No processed images found for SKU: {sku}")
            continue
            
        print(f"\nReviewing SKU {sku} ({sku_idx}/{len(test_skus)}) - Found {len(files)} images...")
        image_paths = [os.path.join(zoom_dir, f) for f in files]
        
        # Create grid image
        cols = min(4, len(files))
        grid = create_grid_image(image_paths, cols=cols, tile_size=500)
        
        grid_save_path = f"scratch/grid_{sku}.jpg"
        grid.save(grid_save_path, "JPEG", quality=85)
        print(f"  Grid image saved to {grid_save_path}")
        
        try:
            review = audit_grid_via_gemini(grid, files, gemini_key)
            print(f"  Status: {review['status'].upper()}")
            print(f"  Feedback: {review['feedback']}")
            if review['failed_items']:
                print(f"  Failed items: {len(review['failed_items'])}")
                for item in review['failed_items']:
                    print(f"    - {item['filename']}: {item['defect']}")
            
            audit_report[sku] = {
                "images": files,
                "review": review,
                "grid_image": grid_save_path
            }
        except Exception as e:
            print(f"  Error auditing SKU {sku}: {e}")
            
        sku_idx += 1
            
    # Save final report to artifacts
    report_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\qa_review_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2)
        
    print("\n==================================================")
    print(f"Audit completed. Report saved to: {report_path}")
    print("==================================================")

if __name__ == "__main__":
    main()
