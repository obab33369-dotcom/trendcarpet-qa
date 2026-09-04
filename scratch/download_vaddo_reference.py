import urllib.request
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
TARGET_PATH = os.path.join(WORKSPACE_DIR, "reforma-original-images", "102612.jpg")

def main():
    url = "https://www.reformasthlm.se/bilder/artiklar/102612.jpg"
    print(f"Downloading {url} to {TARGET_PATH}...")
    try:
        os.makedirs(os.path.dirname(TARGET_PATH), exist_ok=True)
        # Add user-agent header to avoid getting blocked
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            with open(TARGET_PATH, 'wb') as out_file:
                out_file.write(response.read())
        print("Download successful!")
    except Exception as e:
        print(f"Error downloading: {e}")
        # Try another common URL format just in case
        fallback_url = "https://reformasthlm.se/sv/bilder/artiklar/102612.jpg"
        print(f"Trying fallback URL: {fallback_url}...")
        try:
            req = urllib.request.Request(
                fallback_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response:
                with open(TARGET_PATH, 'wb') as out_file:
                    out_file.write(response.read())
            print("Fallback download successful!")
        except Exception as fe:
            print(f"Fallback download also failed: {fe}")

if __name__ == "__main__":
    main()
