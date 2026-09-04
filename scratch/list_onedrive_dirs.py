import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    if not os.path.exists(ONEDRIVE_DIR):
        print(f"Directory not found: {ONEDRIVE_DIR}")
        return
    print(f"Listing subdirectories in: {ONEDRIVE_DIR}...")
    for item in os.listdir(ONEDRIVE_DIR):
        path = os.path.join(ONEDRIVE_DIR, item)
        if os.path.isdir(path):
            # Count files inside
            num_files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
            print(f"  Folder: {item} - Files directly inside: {num_files}")
            # Check for subfolders
            subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
            if subdirs:
                print(f"    Subfolders: {subdirs[:5]}")

if __name__ == "__main__":
    main()
