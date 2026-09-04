import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    target_files = [
        "1639-architectural-digest-styl-047.png",
        "1653-architectural-digest-styl-061.png",
        "1657-architectural-digest-styl-065.png",
        "1661-architectural-digest-styl-069.png"
    ]
    
    print("Searching for specific rendering files...")
    for tf in target_files:
        found_paths = []
        for root, dirs, files in os.walk(ONEDRIVE_DIR):
            if tf in files:
                found_paths.append(os.path.join(root, tf))
                
        print(f"\nFile: {tf}")
        print(f"Found in {len(found_paths)} locations:")
        for p in found_paths:
            print(f"  * {os.path.relpath(p, ONEDRIVE_DIR)}")

if __name__ == "__main__":
    main()
