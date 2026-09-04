import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def list_files(path_name):
    path = os.path.join(ONEDRIVE_DIR, path_name)
    if not os.path.exists(path):
        print(f"Path does not exist: {path_name}")
        return
    print(f"\nFiles in {path_name}:")
    for root, dirs, files in os.walk(path):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), path)
            print(f"  {rel}")

def main():
    list_files(r"Reforma-Full-Catalog-sortering\Matta Seronis - SvartBeige (RG01-1)")
    list_files(r"Reforma-Full-Catalog-sortering-borttagna\Matta Seronis - SvartBeige (RG01-1)")

if __name__ == "__main__":
    main()
