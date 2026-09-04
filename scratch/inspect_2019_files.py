import os
import glob

PROJECT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

files = glob.glob(os.path.join(PROJECT_DIR, "*2019*")) + glob.glob(os.path.join(PROJECT_DIR, "första omgången fyrkantiga", "*2019*"))

for f in files:
    print(f"Path: {f}")
    print(f"Filename: {os.path.basename(f)}")

# Check if they exist in the previous target directory Reforma-interiörer-26-06
target_dir = os.path.join(PROJECT_DIR, "Reforma-interiörer-26-06")
if os.path.exists(target_dir):
    for root, dirs, filenames in os.walk(target_dir):
        for f in filenames:
            if "2019" in f:
                print(f"Found in sorted folder: {os.path.join(root, f)}")
