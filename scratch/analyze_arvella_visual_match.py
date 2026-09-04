import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"

# Path to the user's screenshot
SCREENSHOT_PATH = os.path.join(WORKSPACE_DIR, "scratch", "zara_page.png")  # Wait, let's look for the screenshot uploaded by the user!
# Wait, the user's uploaded image was placed in the artifacts directory or appDataDir?
# In Gemini, the user's uploaded images are typically passed in as prompt context, but wait!
# If the user uploaded an image, can we find it in the artifacts folder?
# Let's search the artifacts directory or appDataDir for any recently added png/jpg file.

def find_uploaded_image():
    # Search ARTIFACTS_DIR and WORKSPACE_DIR for any new image files in the last 2 minutes
    import time
    now = time.time()
    for root, dirs, files in os.walk(ARTIFACTS_DIR):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                p = os.path.join(root, f)
                # If created in the last 300 seconds
                if now - os.path.getmtime(p) < 300:
                    return p
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        if "node_modules" in root or ".git" in root:
            continue
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                p = os.path.join(root, f)
                if now - os.path.getmtime(p) < 300:
                    return p
    return None

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
    uploaded_img = find_uploaded_image()
    if not uploaded_img:
        print("Could not find the uploaded screenshot image.")
        return
        
    print(f"Found uploaded screenshot: {uploaded_img}")
    
    ref_64 = os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG01-64.jpg")
    ref_65 = os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG01-65.jpg")
    ref_66 = os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG01-66.jpg")
    
    screenshot_b64 = encode_image(uploaded_img)
    b64_64 = encode_image(ref_64)
    b64_65 = encode_image(ref_65)
    b64_66 = encode_image(ref_66)
    
    if not all([screenshot_b64, b64_64, b64_65, b64_66]):
        print("Error encoding one or more images.")
        return
        
    parts = [
        {"text": "You are a quality control assistant. Here is a SCREENSHOT from a web browser showing three product cards:\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": screenshot_b64}},
        {"text": "\nThe screenshot shows:\n- Card 1 (left): colorful shapes with green at the top right.\n- Card 2 (middle): colorful shapes with dark grey/black at the top right.\n- Card 3 (right): broken image with title 'Matta Arvella 200x280 cm - Brun'.\n\nBelow are three reference images we have stored for these Arvella carpet SKUs:\n"},
        {"text": "\nReference RG01-64 (associated in our DB with 'Arvella - Brun'):\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": b64_64}},
        {"text": "\nReference RG01-65 (associated with 'Arvella - Röd/Grön'):\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": b64_65}},
        {"text": "\nReference RG01-66 (associated with 'Arvella - Brun/Svart'):\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": b64_66}},
        {"text": "\nPlease analyze these images carefully:\n1. Which Reference image (RG01-64, RG01-65, or RG01-66) visually matches Card 1 (left) in the screenshot? Compare colors, shapes, and patterns.\n2. Which Reference image visually matches Card 2 (middle) in the screenshot?\n3. What does Reference RG01-64 (associated with 'Arvella - Brun') look like visually compared to the other two references?\n4. Is there a mismatch where we have assigned the wrong reference photo to a SKU, or is Card 3 (broken image) the culprit? Explain clearly.\n"}
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
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    main()
