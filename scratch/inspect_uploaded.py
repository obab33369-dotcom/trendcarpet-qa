import os
import json
import base64
import requests

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
    with open(img_path, 'rb') as img_f:
        img_data = base64.b64encode(img_f.read()).decode('utf-8')
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Look at this image of a cowhide on a table. "
        "There is a black smartphone on the table, and there are white cards with digits next to the phone. "
        "1. Where is the black smartphone located in the image (e.g. top-right, bottom-left)? "
        "2. What are the digits written on the cards next to the phone? "
        "3. How should the image be rotated (0, 90, 180, 270 degrees) so that the phone ends up in the bottom-left corner of the image? "
        "Please answer in detail."
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
    img_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\1f2e7c2f-067a-4ff4-9fab-d8c23eca771c\media__1781094385091.jpg"
    print(inspect_image(img_path, key))

if __name__ == "__main__":
    main()
