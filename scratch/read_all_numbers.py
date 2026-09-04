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

def extract_number(img_path, key):
    img = Image.open(img_path)
    img_temp = img.copy()
    img_temp.thumbnail((1000, 1000))
    buffered = BytesIO()
    img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "This is a photo of a cowhide on a table. "
        "Look closely at the white cards with handwritten numbers next to the cowhide. "
        "The cards show digits that form a 3-digit or 4-digit number (for example, 355 or 356). "
        "Please read this number. Double-check the orientation of the digits so you don't read them upside down (for example, '3' at the top, '5' in the middle, '5' at the bottom is '355'). "
        "Return a JSON response: "
        "{\n"
        "  \"number\": \"355\" or similar,\n"
        "  \"digits_read\": [\"3\", \"5\", \"5\"],\n"
        "  \"confidence\": \"high\" | \"medium\" | \"low\"\n"
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
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            return json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip())
        else:
            return {"error": f"HTTP {res.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    key = load_gemini_key()
    if not key:
        print("Gemini API key not found!")
        return
        
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    files = sorted([f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg'))])[:10]
    
    results = {}
    for f in files:
        path = os.path.join(src_dir, f)
        print(f"Scanning {f}...")
        res = extract_number(path, key)
        print(f"  Result: {res}")
        results[f] = res
        
    print("\nScan complete.")

if __name__ == "__main__":
    main()
