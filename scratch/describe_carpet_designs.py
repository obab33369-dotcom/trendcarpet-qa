import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"

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
    images = {
        "Velenna Blå (RG016)": os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG016.jpg"),
        "Velenna Röd/Beige (RG018)": os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG018.jpg"),
        "Arvella Brun (RG01-64)": os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG01-64.jpg"),
        "Arvella Röd/Grön (RG01-65)": os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG01-65.jpg"),
        "Arvella Brun/Svart (RG01-66)": os.path.join(ARTIFACTS_DIR, "00_REFERENCE_RG01-66.jpg")
    }
    
    parts = [{"text": "Please visually describe the design pattern and style of each of the following carpet reference images. Identify which ones show a geometric design with concentric lines (looks like concentric rings or outlines) and which ones show wavy, abstract watercolor-like shapes (blob pattern).\n"}]
    
    for label, path in images.items():
        if os.path.exists(path):
            b64 = encode_image(path)
            if b64:
                parts.append({"text": f"\nReference for {label}:\n"})
                parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})
                
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
            print("=== Design Description ===")
            print(res.json()['candidates'][0]['content']['parts'][0]['text'])
        else:
            print(f"API Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    main()
