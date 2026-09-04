import os

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    print(f"Checking directories in: {TURBOFLOW_ROOT}...")
    for item in sorted(os.listdir(TURBOFLOW_ROOT)):
        path = os.path.join(TURBOFLOW_ROOT, item)
        if os.path.isdir(path):
            # count subfolders
            subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
            # count files recursively
            total_files = 0
            for r, ds, fs in os.walk(path):
                total_files += len(fs)
            print(f"  Folder: {item}")
            print(f"    Subdirs count: {len(subdirs)}, Total files recursively: {total_files}")
            if subdirs:
                print(f"    Sample subdirs: {subdirs[:5]}")

if __name__ == "__main__":
    main()
