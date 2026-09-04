import os
import json
import base64
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def detect_rotation(img_path, key):
    # Retry logic
    max_retries = 3
    backoff = 2
    
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((600, 600))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        return {"error": f"Image load error: {str(e)}"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Look at this image of a cowhide on a table. "
        "There is a black smartphone resting on the table next to some white cards. "
        "1. Where is the black smartphone located (e.g. top-left, top-right, bottom-left, bottom-right)? "
        "2. To rotate the image so that the smartphone ends up in the bottom-left corner of the image, "
        "how many degrees CLOCKWISE should we rotate it? Choose from: 0, 90, 180, 270. "
        "\nReturn a JSON object: "
        "{\n"
        "  \"phone_location\": \"top-right\" | \"top-left\" | \"bottom-right\" | \"bottom-left\",\n"
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
    
    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                return json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip())
            elif res.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                return {"error": f"HTTP {res.status_code}", "detail": res.text}
        except Exception as e:
            time.sleep(backoff)
            backoff *= 2
            if attempt == max_retries - 1:
                return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def read_rotated_ocr(img_path, rotation_angle, key):
    max_retries = 3
    backoff = 2
    
    try:
        img = Image.open(img_path)
        if rotation_angle != 0:
            img_rotated = img.rotate(-rotation_angle, expand=True)
        else:
            img_rotated = img.copy()
            
        img_temp = img_rotated.copy()
        img_temp.thumbnail((1000, 1000))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        return {"error": f"Image load error: {str(e)}"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Focus on the white cards with handwritten numbers next to the black smartphone (which should be in the bottom-left corner). "
        "Read the digits written on these cards from left to right (or top to bottom, depending on orientation). "
        "Do not make assumptions or default to any common number. "
        "Return a JSON response: "
        "{\n"
        "  \"number\": \"311\" or similar,\n"
        "  \"digits_read\": [\"3\", \"1\", \"1\"]\n"
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
    
    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                return json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip())
            elif res.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                return {"error": f"HTTP {res.status_code}", "detail": res.text}
        except Exception as e:
            time.sleep(backoff)
            backoff *= 2
            if attempt == max_retries - 1:
                return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def process_image(img_path, key):
    try:
        rot_data = detect_rotation(img_path, key)
        if "error" in rot_data:
            return {"error": f"Rotation detection error: {rot_data['error']}"}
            
        angle = rot_data.get("rotation_needed_clockwise", 0)
        loc = rot_data.get("phone_location", "unknown")
        
        ocr_res = read_rotated_ocr(img_path, angle, key)
        if "error" in ocr_res:
            return {"error": f"OCR error: {ocr_res['error']}", "phone_location": loc, "rotation_angle": angle}
            
        ocr_res["phone_location"] = loc
        ocr_res["rotation_angle"] = angle
        return ocr_res
    except Exception as e:
        return {"error": str(e)}

def main():
    key = load_gemini_key()
    if not key:
        print("Gemini API key not found!")
        return
        
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    output_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_rotated.json"
    
    files = sorted([f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg'))])
    print(f"Total files to process: {len(files)}")
    
    results = {}
    if os.path.exists(output_json):
        try:
            with open(output_json, 'r', encoding='utf-8') as f_out:
                results = json.load(f_out)
            print(f"Loaded {len(results)} existing results.")
        except Exception:
            pass

    # Filter out already processed files
    files_to_process = [f for f in files if f not in results or "error" in results[f]]
    print(f"Files remaining to process: {len(files_to_process)}")
    
    if not files_to_process:
        print("All files already processed successfully.")
        return

    # Call concurrently with 3 workers
    max_workers = 3
    print(f"Running with {max_workers} concurrent workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_image, os.path.join(src_dir, f), key): f 
            for f in files_to_process
        }
        
        count = 0
        for future in as_completed(future_to_file):
            f = future_to_file[future]
            count += 1
            try:
                res = future.result()
                results[f] = res
                num = res.get('number', 'UNKNOWN') if 'error' not in res else f"ERROR: {res['error']}"
                loc = res.get('phone_location', 'unknown')
                rot = res.get('rotation_angle', 0)
                print(f"[{count}/{len(files_to_process)}] {f} -> {num} (Loc: {loc}, Rot: {rot}°)")
            except Exception as exc:
                print(f"{f} generated an exception: {exc}")
                results[f] = {"error": str(exc)}
                
            # Periodically save results
            if count % 5 == 0:
                with open(output_json, 'w', encoding='utf-8') as f_out:
                    json.dump(results, f_out, indent=2, ensure_ascii=False)
                    
    # Save final results
    with open(output_json, 'w', encoding='utf-8') as f_out:
        json.dump(results, f_out, indent=2, ensure_ascii=False)
        
    print("\nRotation-OCR Scan complete. Results saved.")

if __name__ == "__main__":
    main()
