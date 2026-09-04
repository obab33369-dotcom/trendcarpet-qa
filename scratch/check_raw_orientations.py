import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from rembg import remove, new_session
import numpy as np
import cv2

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

def clean_mask_contours(alpha_np):
    _, thresh = cv2.threshold(alpha_np, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return alpha_np
    largest_contour = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(alpha_np)
    cv2.drawContours(clean_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    return clean_mask

def check_raw_orientation(filename, key, session):
    path = os.path.join(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2", filename)
    img = Image.open(path)
    # NO EXIF transpose
    img_rgba = remove(img, session=session)
    alpha = np.array(img_rgba.split()[3])
    clean_alpha = clean_mask_contours(alpha)
    
    img_rgba_cleaned = Image.merge(
        "RGBA",
        (img.split()[0], img.split()[1], img.split()[2], Image.fromarray(clean_alpha))
    )
    
    preview = Image.new("RGB", img_rgba_cleaned.size, (255, 255, 255))
    preview.paste(img_rgba_cleaned, mask=img_rgba_cleaned.split()[3])
    
    preview.thumbnail((500, 500))
    buffered = BytesIO()
    preview.save(buffered, format="JPEG", quality=85)
    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    # Let's use the Pro model since the user has Pro model active, but we can also use gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Analyze this cleanly segmented photo of a cowhide rug. "
        "The background is white. "
        "We want to know: which direction is the wider 'rump' (where the tail is and the two large hind legs are) pointing? "
        "Is it pointing towards the 'top', 'bottom', 'left', or 'right' of the image? "
        "\n\nReturn a JSON object: "
        "{\n"
        "  \"rump_direction\": \"top\" | \"bottom\" | \"left\" | \"right\"\n"
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
        return json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip())
    else:
        return f"Error: {res.status_code}"

def main():
    key = load_gemini_key()
    session = new_session('u2net')
    
    files = sorted([f for f in os.listdir(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2") if f.lower().endswith(('.jpg', '.jpeg'))])
    
    print("Testing 15 random files from the batch...")
    # Choose 15 files distributed across the batch
    indices = np.linspace(0, len(files)-1, 15, dtype=int)
    for idx in indices:
        f = files[idx]
        res = check_raw_orientation(f, key, session)
        print(f"{f}: {res}")

if __name__ == "__main__":
    main()
