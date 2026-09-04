import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def search_folders_for_prefixes(root_dir, prefixes):
    if not os.path.exists(root_dir):
        print(f"Directory not found: {root_dir}")
        return
        
    found = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            for p in prefixes:
                if file.startswith(f"{p}-") or file.startswith(f"{p}_"):
                    found.append((root, file))
                    
    print(f"\n--- Scanning {os.path.basename(root_dir)} ---")
    if not found:
        print("No files found.")
    for path, file in found:
        # Get relative path from root_dir for readability
        rel = os.path.relpath(path, root_dir)
        print(f"Found: {os.path.join(rel, file)}")

def main():
    prefixes = ["075", "076", "421", "422"]
    search_folders_for_prefixes(os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering"), prefixes)
    search_folders_for_prefixes(os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering-borttagna"), prefixes)

if __name__ == "__main__":
    main()
