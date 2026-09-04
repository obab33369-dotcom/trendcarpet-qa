import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")

if os.path.exists(NEW_WHITE_BG_DIR):
    for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
        if "dion" in root.lower():
            print(f"Files in {root}:")
            for f in sorted(files):
                print(f"  {f}")
else:
    print("NEW_WHITE_BG_DIR does not exist.")
