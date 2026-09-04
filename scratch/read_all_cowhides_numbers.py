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

def extract_number(img_path, key):
    # Retry logic
    max_retries = 5
    backoff = 2
    
    # Load and resize image to reduce upload size
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((1000, 1000))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        return {"error": f"Image load error: {str(e)}"}

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
    
    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                try:
                    res_json = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip())
                    return res_json
                except Exception as parse_err:
                    return {"error": f"Parsing Error: {str(parse_err)}", "raw_text": res.text}
            elif res.status_code == 429:
                # Rate limit hit, backoff and retry
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                return {"error": f"HTTP {res.status_code}", "detail": res.text}
        except Exception as conn_err:
            time.sleep(backoff)
            backoff *= 2
            if attempt == max_retries - 1:
                return {"error": f"Connection Error: {str(conn_err)}"}
                
    return {"error": "Max retries exceeded"}

def main():
    key = load_gemini_key()
    if not key:
        print("Gemini API key not found!")
        return
        
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    output_json = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    
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

    # Use ThreadPoolExecutor for concurrent requests
    # Use 3 workers to stay well under rate limits while keeping speed high
    max_workers = 3
    print(f"Running with {max_workers} concurrent workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(extract_number, os.path.join(src_dir, f), key): f 
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
                print(f"[{count}/{len(files_to_process)}] {f} -> {num}")
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
        
    print("\nScan complete. Results saved.")

if __name__ == "__main__":
    main()
