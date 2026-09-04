import os

TARGET_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-Full-Catalog-sortering"

def main():
    if not os.path.exists(TARGET_DIR):
        print("Folder not found.")
        return
        
    folders = sorted([f for f in os.listdir(TARGET_DIR) if os.path.isdir(os.path.join(TARGET_DIR, f))])
    print(f"Total product folders created: {len(folders)}")
    
    print("\nSample of 20 product folders in the new Full Catalog sorting:")
    for f in folders[:20]:
        path = os.path.join(TARGET_DIR, f)
        files = [x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x)) and not x.startswith("00_REFERENCE_")]
        reserv_path = os.path.join(path, "reserv")
        reserv_count = 0
        if os.path.exists(reserv_path):
            reserv_count = len([x for x in os.listdir(reserv_path) if os.path.isfile(os.path.join(reserv_path, x))])
        print(f"  - {f}: {len(files)} main, {reserv_count} reserv")

if __name__ == "__main__":
    main()
