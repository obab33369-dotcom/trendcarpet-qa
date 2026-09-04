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

def main():
    root_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\1f2e7c2f-067a-4ff4-9fab-d8c23eca771c\.tempmediaStorage"
    files = [os.path.join(root_dir, f) for f in os.listdir(root_dir) if f.lower().endswith(('.jpg', '.png'))]
    if not files:
        print("No media files found")
        return
        
    newest = max(files, key=os.path.getmtime)
    print(f"Newest file: {newest} (size: {os.path.getsize(newest)} bytes, modified: {os.path.getmtime(newest)})")
    
    # Query Gemini to describe it
    key = load_gemini_key()
    with open(newest, 'rb') as img_f:
        img_data = base64.b64encode(img_f.read()).decode('utf-8')
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Focus on the white cards with numbers next to the cowhide. "
        "1. List each card you see from top to bottom. "
        "2. What digit is written on each card? "
        "3. Read the digits as a single number and print the final number."
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
        print(res.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"Error: {res.status_code} - {res.text}")

if __name__ == "__main__":
    main()
