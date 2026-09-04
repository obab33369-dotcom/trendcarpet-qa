import os

TARGET_PARENT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering"

# Look for any folder containing "lucca"
for d in os.listdir(TARGET_PARENT):
    if "lucca" in d.lower():
        path = os.path.join(TARGET_PARENT, d)
        print(f"\n=== Folder: {d} ===")
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        print(f"Total files: {len(files)}")
        for f in sorted(files)[:10]:
            print(f"  - {f}")
        
        reserv = os.path.join(path, "reserv")
        if os.path.exists(reserv):
            print(f"Total reserv files: {len(os.listdir(reserv))}")
