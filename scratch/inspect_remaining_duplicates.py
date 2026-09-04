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

def inspect_image_rotated(img_path, key):
    img = Image.open(img_path)
    img_temp = img.copy()
    img_temp.thumbnail((600, 600))
    buffered = BytesIO()
    img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Look at this image. Where is the black smartphone located? "
        "How many degrees CLOCKWISE should we rotate it so the smartphone is in the bottom-left corner? Choose from 0, 90, 180, 270. "
        "\nReturn a JSON object: "
        "{\n"
        "  \"rotation_needed_clockwise\": 0 | 90 | 180 | 270\n"
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
    angle = 0
    if res.status_code == 200:
        angle = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip()).get("rotation_needed_clockwise", 0)
        
    if angle != 0:
        img_rot = img.rotate(-angle, expand=True)
    else:
        img_rot = img.copy()
        
    img_temp = img_rot.copy()
    img_temp.thumbnail((1200, 1200))
    buffered = BytesIO()
    img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    prompt_ocr = (
        "Focus on the white cards with handwritten numbers next to the smartphone (which is in the bottom-left). "
        "1. List each card from top to bottom (or left to right). "
        "2. What digit is written on each card? "
        "3. Read the digits as a single number and print the final number."
    )
    
    data_ocr = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_ocr},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.0
        }
    }
    
    res_ocr = requests.post(url, headers=headers, json=data_ocr, timeout=30)
    if res_ocr.status_code == 200:
        return f"Rotation angle: {angle}°\n" + res_ocr.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {res_ocr.status_code}"

def main():
    key = load_gemini_key()
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    
    files = ["NSPM3714.JPG", "OTYL1698.JPG", "HCHH1324.JPG", "DGJR8081.JPG", "KWHA5687.JPG", "YLBS5372.JPG", "RXSA5233.JPG"]
    
    for f in files:
        print(f"\n=== INSPECTING {f} ===")
        path = os.path.join(src_dir, f)
        if os.path.exists(path):
            print(inspect_image_rotated(path, key))
        else:
            print(f"File not found: {path}")

if __name__ == "__main__":
    main()
