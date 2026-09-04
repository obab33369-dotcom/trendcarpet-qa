import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    print("Searching for 'NEWCASTLE-BLACK' in all folders under turboflow...")
    
    found_paths = []
    for root, dirs, files in os.walk(ONEDRIVE_DIR):
        # Check dirs
        for d in dirs:
            if "newcastle-black" in d.lower() or "newcastle" in d.lower():
                found_paths.append(("dir", os.path.join(root, d)))
        # Check files
        for f in files:
            if "newcastle-black" in f.lower() or "newcastle" in f.lower():
                found_paths.append(("file", os.path.join(root, f)))
                
    print(f"Found {len(found_paths)} matches:")
    for t, p in found_paths:
        print(f"  * [{t.upper()}] {os.path.relpath(p, ONEDRIVE_DIR)}")

if __name__ == "__main__":
    main()
