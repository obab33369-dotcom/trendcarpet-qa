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

def inspect_image(img_path, key):
    img = Image.open(img_path)
    img_temp = img.copy()
    img_temp.thumbnail((1200, 1200))
    buffered = BytesIO()
    img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Analyze this image. It shows a cowhide rug on a table. "
        "There are white cards with digits on them placed on the table next to the cowhide. "
        "1. Describe all white cards you see. What digit is written on each card? "
        "2. How are the cards arranged (horizontally, vertically, stacked)? "
        "3. Read the digits in order to form a full number (for example, if cards are stacked vertically showing 3, then 5, then 5, read it as 355). "
        "Explain your reasoning step-by-step."
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
    
    res = requests.post(url, headers=headers, json=data, timeout=30)
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {res.status_code} - {res.text}"

def main():
    key = load_gemini_key()
    img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup\AHIN4169.JPG"
    print(inspect_image(img_path, key))

if __name__ == "__main__":
    main()
