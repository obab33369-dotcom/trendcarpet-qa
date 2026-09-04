import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def scan_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return
    print(f"\nScanning: {folder_path}")
    for item in os.listdir(folder_path):
        path = os.path.join(folder_path, item)
        if os.path.isfile(path):
            print(f"  File: {item}")
        elif os.path.isdir(path):
            print(f"  Subfolder: {item}/")
            for subitem in os.listdir(path):
                print(f"    File: {subitem}")

def main():
    dirs = [
        os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering"),
        os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
    ]
    
    for d in dirs:
        print(f"\n================ SCANNING {os.path.basename(d)} ================")
        for folder in os.listdir(d):
            if "prime" in folder.lower() or "sakai" in folder.lower():
                scan_folder(os.path.join(d, folder))

if __name__ == "__main__":
    main()
