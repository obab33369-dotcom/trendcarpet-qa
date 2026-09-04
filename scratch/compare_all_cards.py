import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image

def load_gemini_key():
    env_path = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

def describe_cards(img_path, key):
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((1200, 1200))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        return f"Error loading image: {e}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "We are verifying handwritten number cards in this photo. "
        "1. Locate the white cards. "
        "2. Describe the orientation of the numbers relative to the camera (are they upright, upside-down, or rotated 90 degrees?). "
        "3. Read the digits as they appear right-side up relative to the camera perspective. "
        "4. What is the correct 3-digit number from the camera perspective?"
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
            "temperature": 0.0
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"HTTP {res.status_code}: {res.text}"
    except Exception as e:
        return f"Request error: {e}"

def main():
    key = load_gemini_key()
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    
    files = [
        "WKFI6689.JPG", "WYGV2057.JPG", "AGJM5060.JPG", "AHIN4169.JPG", 
        "CSKG8106.JPG", "FWBU1032.JPG", "FZLK0753.JPG", "GDQV3716.JPG", 
        "HRKU8965.JPG", "NNRK8041.JPG", "RDIK1368.JPG", "TNML9192.JPG", 
        "VKTJ0424.JPG", "RXSA5233.JPG"
    ]
    
    for f in files:
        print(f"\n=========================================")
        print(f"DESCRIBING: {f}")
        print(f"=========================================")
        path = os.path.join(src_dir, f)
        if os.path.exists(path):
            result = describe_cards(path, key)
            print(result)
        else:
            print(f"File not found: {path}")

if __name__ == "__main__":
    main()
