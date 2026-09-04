import os

PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

def main():
    if not os.path.exists(PICTURES_DIR):
        print(f"Directory not found: {PICTURES_DIR}")
        return
        
    print(f"Listing directories in: {PICTURES_DIR}...")
    for item in os.listdir(PICTURES_DIR):
        path = os.path.join(PICTURES_DIR, item)
        if os.path.isdir(path):
            print(f"  Folder: {item}")
            # Check for subdirs or count files directly inside
            try:
                files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
                print(f"    Files: {len(files)}, Subdirs: {len(subdirs)}")
                if subdirs:
                    print(f"    Subdirs: {subdirs[:5]}")
            except Exception as e:
                print(f"    Error: {e}")

if __name__ == "__main__":
    main()
