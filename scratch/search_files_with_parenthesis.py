import os
import re
import datetime

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    if not os.path.exists(ONEDRIVE_DIR):
        print(f"OneDrive directory not found: {ONEDRIVE_DIR}")
        return
        
    print(f"Scanning OneDrive: {ONEDRIVE_DIR} for files containing '(1)'...")
    
    found = []
    for root, dirs, files in os.walk(ONEDRIVE_DIR):
        # Skip some dirs to be clean
        if "Reforma-interiörer-ny-sortering" in root:
            continue
        for f in files:
            if "(1)" in f or " (1)" in f:
                path = os.path.join(root, f)
                try:
                    stat = os.stat(path)
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                    found.append((f, mtime, path))
                except Exception:
                    pass
                    
    print(f"Total files with '(1)' found: {len(found)}")
    found.sort(key=lambda x: x[1])
    
    for f, mtime, path in found[:30]:
        rel = os.path.relpath(path, ONEDRIVE_DIR)
        print(f"  {rel} - Modified: {mtime}")
        
    if len(found) > 30:
        print(f"  ... showing first 30 of {len(found)}")

if __name__ == "__main__":
    main()
