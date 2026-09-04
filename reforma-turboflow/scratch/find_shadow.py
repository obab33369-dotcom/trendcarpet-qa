import os
import base64
import requests
import json

GEMINI_ENV = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

def load_gemini_key():
    if not os.path.exists(GEMINI_ENV):
        return None
    with open(GEMINI_ENV, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                if k.strip() == "GEMINI_API_KEY":
                    return v.strip().strip('"').strip("'")
    return None

GEMINI_API_KEY = load_gemini_key()
if not GEMINI_API_KEY:
    print("API key not found")
    exit(1)

test_skus = ["107482", "018-natural", "102084", "010-natural"]
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent?key={GEMINI_API_KEY}"
headers = {"Content-Type": "application/json"}

for sku in test_skus:
    p = f"C:\\Users\\AndronikLindgren\\OneDrive - CaMa Gruppen AB\\Pictures\\turboflow\\ftp_upload_cropped_full\\backup_before_correction\\{sku}_1.jpg"
    if not os.path.exists(p):
        p = f"C:\\Users\\AndronikLindgren\\OneDrive - CaMa Gruppen AB\\Pictures\\turboflow\\ftp_upload_cropped_full\\backup_before_correction\\{sku}.jpg"
    if os.path.exists(p):
        with open(p, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
        data = {
            "contents": [{
                "parts": [
                    {"text": "Does this original product image have a visible floor shadow underneath the furniture? Answer with YES or NO and a very brief description."},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                ]
            }]
        }
        res = requests.post(url, headers=headers, json=data)
        if res.status_code == 200:
            print(f"{sku}:", res.json()["candidates"][0]["content"]["parts"][0]["text"].strip())
        else:
            print(f"Error {sku}: {res.status_code}")
