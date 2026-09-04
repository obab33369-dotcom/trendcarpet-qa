import os
import hashlib

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def get_hash(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return "ERROR"

def main():
    files = [
        os.path.join(WORKSPACE_DIR, "reforma-original-images", "RG01-85.jpg"),
        os.path.join(WORKSPACE_DIR, "reforma-original-images", "RG01-855.jpg"),
        os.path.join(WORKSPACE_DIR, "reforma-original-images", "2113_matta-ventaro-rod-multi.jpg"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", "RG01-85.jpg"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", "RG01-855.jpg"),
    ]
    
    for f in files:
        h = get_hash(f)
        if h:
            print(f"File: {os.path.basename(f)}")
            print(f"  Path: {f}")
            print(f"  Hash: {h}")
        else:
            print(f"File does not exist: {os.path.basename(f)}")

if __name__ == "__main__":
    main()
