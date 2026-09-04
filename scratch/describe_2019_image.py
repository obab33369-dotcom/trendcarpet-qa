import os
import sys
import json
import base64
from PIL import Image
from io import BytesIO
import requests

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
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

GEMINI_API_KEY = load_gemini_key()

def encode_image(img_path, max_size=800):
    img = Image.open(img_path)
    img_temp = img.copy()
    img_temp.thumbnail((max_size, max_size))
    buffered = BytesIO()
    img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def query_gemini_describe(img_path):
    img_b64 = encode_image(img_path)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    prompt = "Describe the main furniture pieces present in this image (e.g. is it a dining table and chairs, or a chest of drawers/byrå? List colors and materials)."
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}
                ]
            }
        ],
        "generationConfig": {"temperature": 0.1}
    }
    res = requests.post(url, headers=headers, json=data, timeout=30)
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    return f"Error: {res.status_code} - {res.text}"

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\1973-architectural-digest-styl-183.png"
if os.path.exists(img_path):
    desc = query_gemini_describe(img_path)
    print("=== Description of 2019-architectural-digest-styl-229.png ===")
    print(desc)
else:
    print("Image not found")
