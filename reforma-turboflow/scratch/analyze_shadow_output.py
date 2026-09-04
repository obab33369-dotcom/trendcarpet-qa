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

def analyze_shadow_output(img_path, name):
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
                            f"Analyze this processed image: '{name}'. "
                            "The original image had a soft floor shadow underneath the wooden table. "
                            "Examine the processed image carefully and tell me: "
                            "1. Does this processed image preserve the original floor shadow underneath the table? "
                            "2. If yes, describe the shadow's appearance. Is it a clean, neutral gray shadow with no warm/brown color cast? "
                            "3. Does the shadow blend smoothly into the pure white background without any visible rectangular seams or borders? "
                            "4. Does the table itself retain its natural warm wood colors and sharp edges?"
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
        print(f"\n--- Shadow Output Analysis of {name} ---")
        print(text)
    else:
        print(f"Error {res.status_code}: {res.text}")

analyze_shadow_output(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\test_composite_018-natural.jpg", "test_composite_018-natural.jpg")
