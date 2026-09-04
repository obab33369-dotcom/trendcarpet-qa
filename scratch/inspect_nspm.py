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

def describe_cards_simple(img_path, key):
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((1200, 1200))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Focus on the white cards with handwritten numbers next to the phone. "
        "List the digit written on each card from top to bottom. "
        "Read the digits as a single 3-digit number from top to bottom."
    )
    
    data = {
        "contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}]}],
        "generationConfig": {"temperature": 0.0}
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error HTTP {res.status_code}"
    except Exception as e:
        return f"Error: {e}"

def main():
    key = load_gemini_key()
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    
    files = ["NSPM3714.JPG", "KLPD8550.JPG", "OTYL1698.JPG"]
    for f in files:
        print(f"\n=== {f} ===")
        path = os.path.join(src_dir, f)
        if os.path.exists(path):
            print(describe_cards_simple(path, key))
        else:
            print("Not found")

if __name__ == "__main__":
    main()
