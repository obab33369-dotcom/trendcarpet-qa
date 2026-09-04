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

def analyze_image(img_path, name):
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
                            f"Analyze this image: '{name}'. The user says 'möbeln är delvis avtonad' "
                            "(the furniture is partially faded/desaturated/transparent). "
                            "Examine the image carefully and tell me: "
                            "1. What specific parts of the furniture look faded, grayed out, or washed out? "
                            "2. Is it because the edges of the furniture are fading to white, or because parts of the furniture body (like the top, legs, or drawer fronts) have lost their color and turned gray/white? "
                            "Describe the exact visual appearance of the fading."
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
        print(f"\n--- Analysis of {name} ---")
        print(text)
    else:
        print(f"Error {res.status_code}: {res.text}")

analyze_image(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\test_composite_2105.jpg", "test_composite_2105.jpg")
analyze_image(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\test_composite_19011.jpg", "test_composite_19011.jpg")
