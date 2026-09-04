import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def is_carpet(folder_name):
    # Carpet folders usually have "matta", "rug", "rg01", "jute", "pet" in their name or SKU
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def scan_dir(root_name):
    path = os.path.join(ONEDRIVE_DIR, root_name)
    if not os.path.exists(path):
        print(f"Directory {root_name} does not exist.")
        return []
    
    carpets = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            if is_carpet(item):
                carpets.append(item)
    return carpets

def main():
    for root in ["Reforma-Full-Catalog-sortering", "Reforma-Full-Catalog-sortering-borttagna", "Reforma-interiörer-ny-sortering", "Reforma-interiörer-ny-sortering-borttagna"]:
        carpets = scan_dir(root)
        print(f"\nCarpets in {root} ({len(carpets)}):")
        for c in carpets:
            print(f"  {c}")

if __name__ == "__main__":
    main()
