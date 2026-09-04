import os
import json
import base64
import requests
import time
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

def verify_single_image(img_path, key):
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((1200, 1200))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        return {"error": f"Image load error: {str(e)}"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    # Prompt without using 355 as an example to avoid model bias
    prompt = (
        "Focus on the white cards/labels placed next to the cowhide on the table. "
        "There are numbers/digits written on these cards. "
        "Please read them carefully from top to bottom (or left to right, depending on layout). "
        "Do not make assumptions or default to any common number. "
        "Return a JSON response: "
        "{\n"
        "  \"number\": \"detected_number\",\n"
        "  \"digits_read\": [\"digit1\", \"digit2\", ...],\n"
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
            return {"error": f"HTTP {res.status_code}", "detail": res.text}
    except Exception as e:
        return {"error": str(e)}

def main():
    key = load_gemini_key()
    output_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_rotated.json"
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    
    if not os.path.exists(output_json):
        print("Results file not found")
        return
        
    with open(output_json, 'r', encoding='utf-8') as f:
        results = json.load(f)
        
    # Analyze frequency of each number
    counts = {}
    for filename, data in results.items():
        if "error" in data:
            continue
        num = data.get("number")
        counts[num] = counts.get(num, []) + [filename]
        
    print("=== NUMBER FREQUENCIES ===")
    duplicates = {}
    for num, files in sorted(counts.items()):
        print(f"Number {num}: {len(files)} files -> {files}")
        if len(files) > 1:
            duplicates[num] = files
            
    # Errors
    errors = [filename for filename, data in results.items() if "error" in data]
    print(f"\nErrors found: {errors}")
    
    # We will re-run duplicate resolution and errors
    to_reverify = []
    for num, files in duplicates.items():
        to_reverify.extend(files)
    to_reverify.extend(errors)
    
    # Also reverify suspicious 4-digit numbers
    suspicious_4digit = [filename for filename, data in results.items() if not "error" in data and len(data.get("number", "")) > 3]
    print(f"Suspicious 4-digit numbers: {suspicious_4digit}")
    to_reverify.extend(suspicious_4digit)
    
    # Deduplicate list to reverify
    to_reverify = list(set(to_reverify))
    print(f"\nTotal files to reverify: {len(to_reverify)}")
    
    if not to_reverify:
        print("No files need reverification.")
        return
        
    for f in sorted(to_reverify):
        path = os.path.join(src_dir, f)
        print(f"Re-verifying {f}...")
        res = verify_single_image(path, key)
        print(f"  Old: {results.get(f, {}).get('number', 'ERROR')}")
        print(f"  New: {res.get('number', 'ERROR') if 'error' not in res else 'ERROR: ' + res['error']}")
        if "error" not in res:
            results[f] = res
            
    # Save back
    with open(output_json, 'w', encoding='utf-8') as f_out:
        json.dump(results, f_out, indent=2, ensure_ascii=False)
        
    print("\nRe-verification completed and results updated.")

if __name__ == "__main__":
    main()
