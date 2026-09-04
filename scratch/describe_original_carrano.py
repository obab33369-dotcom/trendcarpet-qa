import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
img_path = os.path.join(WORKSPACE_DIR, "reforma-original-images", "RG01-71.jpg")
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
        print(f"Error encoding: {e}")
        return None

if not os.path.exists(img_path):
    print(f"Image not found: {img_path}")
    sys.exit(0)

b64 = encode_image(img_path)
if b64:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    parts = [
        {"text": "Please analyze this product image of a carpet and tell me:\n1. What is the pattern style (e.g. checkerboard, stripes, organic, etc.)?\n2. What are the dominant colors in the pattern?\n3. Does this look like a Green carpet, or a Brown/White carpet?\n"},
        {"inlineData": {"mimeType": "image/jpeg", "data": b64}}
    ]
    data = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.0}
    }
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        print("Gemini Description:")
        print(res.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"API Error {res.status_code}: {res.text}")
