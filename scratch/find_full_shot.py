import os
import json
import base64
import requests
from PIL import Image
from io import BytesIO

ENV_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
ZOOM_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images\artiklar\zoom"

def load_gemini_key():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

def check_image(img_path, key):
    with Image.open(img_path) as img:
        img = img.resize((500, 500), Image.Resampling.LANCZOS)
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Look at this product image. Is it a close-up/detail shot showing only a surface or part of the product, "
        "or is it a full shot of the furniture item? Answer in JSON format:\n"
        "{\n"
        "  \"is_full_shot\": true | false,\n"
        "  \"description\": \"Explain what is visible\"\n"
        "}"
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
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    res = requests.post(url, headers=headers, json=data, timeout=30)
    if res.status_code == 200:
        try:
            text_resp = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            return json.loads(text_resp)
        except Exception as e:
            return {"is_full_shot": False, "description": str(e)}
    return {"is_full_shot": False, "description": res.text}

def main():
    key = load_gemini_key()
    if not key:
        print("Key not found")
        return
        
    for i in range(1, 6):
        path = os.path.join(ZOOM_DIR, f"107313_{i}.jpg")
        if os.path.exists(path):
            res = check_image(path, key)
            print(f"Slot {i}: Full shot={res.get('is_full_shot')} - {res.get('description')}")
        else:
            print(f"Slot {i}: Does not exist")

if __name__ == "__main__":
    main()
