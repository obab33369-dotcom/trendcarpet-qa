import os
import json
import base64
import requests
from PIL import Image
from io import BytesIO

V3_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\artiklar"
ENV_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
REPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\bad_crops_report.json"

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

def query_gemini_about_image(img_path, key):
    with Image.open(img_path) as img:
        # Resize to 500x500 for fast API call
        img = img.resize((500, 500), Image.Resampling.LANCZOS)
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Look at this product image. Is the main furniture item physically cut off/cropped at the edges of the image? "
        "For example, are the legs cut off at the bottom, or is the top/sides cut off?\n"
        "Please classify it as one of the following:\n"
        "1. 'COMPLETE': The product is fully visible and not cut off at all.\n"
        "2. 'CUT_OFF_DETAIL': The product is a detail/close-up view (e.g. showing only the tabletop wood, or a shelf mechanism, or drawer close-up) so it is naturally cropped.\n"
        "3. 'CUT_OFF_BAD': The product is a full shot but got cut off at the edge (e.g. legs are clipped at the very bottom, or the top of the backrest touches/goes past the top edge).\n\n"
        "Answer in JSON format:\n"
        "{\n"
        "  \"classification\": \"COMPLETE\" | \"CUT_OFF_DETAIL\" | \"CUT_OFF_BAD\",\n"
        "  \"reason\": \"Explain why\"\n"
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
            return {"classification": "ERROR", "reason": str(e)}
    else:
        return {"classification": "ERROR", "reason": res.text}

def main():
    key = load_gemini_key()
    if not key:
        print("Key not found")
        return
        
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        bad_images = json.load(f)
        
    print(f"Inspecting {len(bad_images)} failed images...")
    results = {}
    for item in bad_images:
        filename = item.get("filename")
        img_path = os.path.join(V3_DIR, filename)
        if not os.path.exists(img_path):
            print(f"File {filename} does not exist at {img_path}")
            continue
            
        print(f"Inspecting {filename}...")
        res = query_gemini_about_image(img_path, key)
        print(f"  Result: {res.get('classification')} - {res.get('reason')}")
        results[filename] = res
        
    with open(r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\failed_inspected.json", 'w', encoding='utf-8') as f_out:
        json.dump(results, f_out, indent=2)

if __name__ == "__main__":
    main()
