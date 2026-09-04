import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    target_files = [
        "2201-architectural-digest-styl-088.png",
        "2208-architectural-digest-styl-095.png",
        "2285-architectural-digest-styl-172.png",
        "2292-architectural-digest-styl-179.png",
        "2299-architectural-digest-styl-186.png",
        "2334-architectural-digest-styl-221.png",
        "2295-architectural-digest-styl-182.png",
        "2337-architectural-digest-styl-224.png"
    ]
    
    print("Searching for the 8 matched Newcastle rendering files...")
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
