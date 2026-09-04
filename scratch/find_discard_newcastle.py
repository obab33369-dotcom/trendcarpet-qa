import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def main():
    print("Scanning clean root for Newcastle...")
    if os.path.exists(CLEAN_ROOT):
        for d in os.listdir(CLEAN_ROOT):
            if "newcastle" in d.lower():
                print(f"  * {d}")
                
    print("\nScanning discard root for Newcastle...")
    if os.path.exists(DISCARD_ROOT):
        for d in os.listdir(DISCARD_ROOT):
            if "newcastle" in d.lower():
                print(f"  * {d}")

if __name__ == "__main__":
    main()
