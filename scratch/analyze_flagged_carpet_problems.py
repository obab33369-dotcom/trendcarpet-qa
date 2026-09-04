import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
CLEAN_ROOT = os.path.join(WORKSPACE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(WORKSPACE_DIR, "Reforma-Mattor-sortering-borttagna")
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

def analyze_mismatch(folder_name):
    clean_path = os.path.join(CLEAN_ROOT, folder_name)
    discard_path = os.path.join(DISCARD_ROOT, folder_name)
    
    # Get reference photo
    ref_photo = None
    for f in os.listdir(clean_path):
        if f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png')):
            ref_photo = os.path.join(clean_path, f)
            break
            
    if not ref_photo:
        return folder_name, "No reference photo found in folder."
        
    # Get one discarded rendering
    discarded_renders = [f for f in os.listdir(discard_path) if not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    if not discarded_renders:
        return folder_name, "No discarded renderings found."
        
    render_photo = os.path.join(discard_path, discarded_renders[0])
    
    ref_b64 = encode_image(ref_photo)
    render_b64 = encode_image(render_photo)
    
    if not ref_b64 or not render_b64:
        return folder_name, "Error encoding images."
        
    parts = [
        {"text": f"You are a quality control assistant analyzing carpet designs. Here is the REFERENCE image for carpet product '{folder_name}':\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": ref_b64}},
        {"text": "\nHere is a CANDIDATE room rendering that was discarded because the carpet didn't match the reference:\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": render_b64}},
        {"text": "\nPlease analyze the visual difference and explain:\n1. What design pattern and colors are shown in the REFERENCE image?\n2. What design pattern and colors are shown in the room rendering carpet?\n3. Explain the mismatch. Are they completely different designs, or just different colors of the same design, or did the wrong carpet get rendered? Try to identify if the rendering is correct for a different well-known design (e.g. Arvella, Velenna, Sorvento, etc.).\nKeep your response concise (3-4 sentences).\n"}
    ]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.0
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=60)
        if res.status_code == 200:
            analysis = res.json()['candidates'][0]['content']['parts'][0]['text']
            return folder_name, analysis
        return folder_name, f"API Error: {res.status_code}"
    except Exception as e:
        return folder_name, f"Error: {e}"

def main():
    # List of the 21 folders found to have 0 kept images
    folders_to_analyze = [
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
    
    print(f"Starting visual mismatch analysis on {len(folders_to_analyze)} folders...")
    
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_mismatch, f): f for f in folders_to_analyze}
        for future in as_completed(futures):
            folder = futures[future]
            try:
                folder_name, analysis = future.result()
                results[folder_name] = analysis
                print(f"Finished analysis for: {folder_name}")
            except Exception as e:
                print(f"Error for {folder}: {e}")
                
    # Save the report
    report_path = os.path.join(PROJECT_DIR, "scratch", "carpet_mismatch_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved report to {report_path}")
    
    # Print a text summary
    print("\n=== SUMMARY OF CARPET DESIGN MISMATCHES ===")
    for folder in sorted(results.keys()):
        print(f"\n* Folder: {folder}")
        print(results[folder])
        print("-" * 60)

if __name__ == "__main__":
    main()
