import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    paths = [
        r"Reforma-Full-Catalog-sortering\Matta Ventaro - RödMulti (RG01-85)",
        r"Reforma-Full-Catalog-sortering-borttagna\Matta Ventaro - RödMulti (RG01-85)"
    ]
    for p in paths:
        full_path = os.path.join(ONEDRIVE_DIR, p)
        if os.path.exists(full_path):
            print(f"\nFiles in {p}:")
            for root, dirs, files in os.walk(full_path):
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), full_path)
                    print(f"  {rel}")
        else:
            print(f"Directory does not exist: {p}")

if __name__ == "__main__":
    main()
