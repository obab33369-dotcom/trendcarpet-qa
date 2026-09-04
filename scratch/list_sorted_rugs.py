import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def scan_folders(root):
    if not os.path.exists(root):
        print(f"Dir not found: {root}")
        return
    for item in sorted(os.listdir(root)):
        if "matta" in item.lower():
            path = os.path.join(root, item)
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            reserv_path = os.path.join(path, "reserv")
            reserv_files = []
            if os.path.exists(reserv_path):
                reserv_files = [f for f in os.listdir(reserv_path) if os.path.isfile(os.path.join(reserv_path, f))]
            print(f"Folder: {item}")
            print(f"  Main files ({len(files)}): {files[:5]}...")
            if reserv_files:
                print(f"  Reserv files ({len(reserv_files)}): {reserv_files[:5]}...")

print("=== CLEAN FOLDERS ON ONEDRIVE ===")
scan_folders(TARGET_DIR)

print("\n=== DISCARDED FOLDERS ON ONEDRIVE ===")
scan_folders(DISCARD_DIR)
