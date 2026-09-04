import os
import requests

GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

def load_gemini_key():
    if os.path.exists(GEMINI_KEY_PATH):
        with open(GEMINI_KEY_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return os.environ.get("GEMINI_API_KEY", "")

def main():
    key = load_gemini_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    res = requests.get(url)
    if res.status_code == 200:
        models = res.json().get("models", [])
        for m in models:
            print(f"Name: {m['name']} | Supported: {m.get('supportedGenerationMethods')}")
    else:
        print(f"Error: {res.status_code} - {res.text}")

if __name__ == "__main__":
    main()
