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

def analyze_original(img_path, name):
    with open(img_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode('utf-8')
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Analyze this original image: '{name}'. "
                            "Please examine the background and the area underneath the furniture carefully. "
                            "1. Does this furniture have a floor shadow underneath it in this original image? "
                            "2. If yes, what does the shadow look like (is it soft, dark, faint, large, etc.)? "
                            "3. If no, is the background a flat, clean white, or does it have a slight off-white color?"
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_data
                        }
                    }
                ]
            }
        ]
    }
    
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        print(f"\n--- Original Analysis of {name} ---")
        print(text)
    else:
        print(f"Error {res.status_code}: {res.text}")

analyze_original(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\backup_before_correction\2105_1.jpg", "2105_1.jpg")
analyze_original(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\backup_before_correction\19011_1.jpg", "19011_1.jpg")
