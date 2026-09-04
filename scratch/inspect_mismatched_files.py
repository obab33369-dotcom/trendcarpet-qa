import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    prefixes = ["2087", "2089", "2104", "2113"]
    
    roots = [
        "Reforma-Full-Catalog-sortering",
        "Reforma-Full-Catalog-sortering-borttagna",
        "Reforma-interiörer-ny-sortering",
        "Reforma-interiörer-ny-sortering-borttagna"
    ]
    
    for prefix in prefixes:
        print(f"\nSearching for prefix: {prefix}")
        found = False
        for root in roots:
            path = os.path.join(ONEDRIVE_DIR, root)
            if not os.path.exists(path):
                continue
            for root_dir, dirs, files in os.walk(path):
                for f in files:
                    if f.startswith(prefix + "_") or f.startswith(prefix + "-"):
                        rel_path = os.path.relpath(os.path.join(root_dir, f), ONEDRIVE_DIR)
                        print(f"  Found: {rel_path}")
                        found = True
        if not found:
            print("  No files found.")

if __name__ == "__main__":
    main()
