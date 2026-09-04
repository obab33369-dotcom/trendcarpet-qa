import os
import urllib.request

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_PATH = os.path.join(WORKSPACE_DIR, "reforma-original-images", "9965.jpg")

def main():
    dirs = [
        os.path.join(WORKSPACE_DIR, "reforma-original-images"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar")
    ]
    
    found = False
    for d in dirs:
        p = os.path.join(d, "9965.jpg")
        if os.path.exists(p):
            print(f"Found Sakai image at: {p}")
            found = True
            break
            
    if not found:
        print("Sakai reference image not found locally. Downloading...")
        url = "https://www.reformasthlm.se/bilder/artiklar/9965.jpg"
        try:
            os.makedirs(os.path.dirname(TARGET_PATH), exist_ok=True)
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

if __name__ == "__main__":
    main()
