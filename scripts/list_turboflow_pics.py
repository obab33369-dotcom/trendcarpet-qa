import os

PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

if not os.path.exists(PICS_DIR):
    print(f"Directory not found: {PICS_DIR}")
else:
    files = sorted(os.listdir(PICS_DIR))
    print(f"Total files in directory: {len(files)}")
    print("First 30 files:")
    for f in files[:30]:
        print(f"  {f}")
