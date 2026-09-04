import os

PROJECT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

for root, dirs, files in os.walk(PROJECT_DIR):
    if "Reforma-interiörer-ny-sortering" in root or "Reforma-interiörer-26-06" in root:
        continue
    for f in files:
        if f.startswith("033-") or f.startswith("034-") or f.startswith("087-") or f.startswith("088-"):
            print(os.path.join(root, f))
