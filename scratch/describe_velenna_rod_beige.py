import os
import shutil
import base64
import requests
import json
from io import BytesIO
from PIL import Image

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"

# Target carpet root
CLEAN_ROOT = os.path.join(WORKSPACE_DIR, "Reforma-Mattor-sortering")
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

def main():
    # Find RG018 folder and copy 00_REFERENCE_RG018.jpg
    src_file = None
    for item in os.listdir(CLEAN_ROOT):
        if "(RG018)" in item:
            folder_path = os.path.join(CLEAN_ROOT, item)
            for f in os.listdir(folder_path):
                if f.startswith("00_REFERENCE_"):
                    src_file = os.path.join(folder_path, f)
                    break
            break
            
    if not src_file:
        print("Could not find RG018 reference image.")
        return
        
    dest_file = os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG018.jpg")
    shutil.copy2(src_file, dest_file)
    print(f"Copied {src_file} to {dest_file}")
    
    # Find the user's screenshot
    import time
    now = time.time()
    screenshot_path = None
    for root, dirs, files in os.walk(ARTIFACTS_DIR):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "media__" in f:
                screenshot_path = os.path.join(root, f)
                break
                
    if not screenshot_path:
        print("Could not find user's screenshot.")
        return
        
    print(f"Screenshot path: {screenshot_path}")
    
    b64_ref = encode_image(dest_file)
    b64_screenshot = encode_image(screenshot_path)
    
    parts = [
        {"text": "You are a quality control assistant. Here is a SCREENSHOT from a web browser showing three product cards:\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": b64_screenshot}},
        {"text": "\nHere is the reference image for 'Matta Velenna - Röd/Beige' (SKU: RG018):\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": b64_ref}},
        {"text": "\nPlease analyze these images:\n1. Describe the design pattern, shape style, and colors of the 'Matta Velenna - Röd/Beige' reference photo.\n2. Does this reference photo match Card 1 (left) or Card 2 (middle) in the screenshot? Compare them visually.\n3. Based on this, is the 'Matta Velenna' series the one with the watercolor-like blob pattern, and is Card 1 or Card 2 actually Velenna?\n"}
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
            print("=== Gemini Analysis Result ===")
            print(res.json()['candidates'][0]['content']['parts'][0]['text'])
        else:
            print(f"API Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
