import os

fix_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"

print("Searching for 'milou' or '1400034' in", fix_dir)
for root, dirs, files in os.walk(fix_dir):
    for d in dirs:
        if "milou" in d.lower() or "1400034" in d.lower():
            print("Found folder:", os.path.join(root, d))
    for f in files:
        if "milou" in f.lower() or "1400034" in f.lower():
            print("Found file:", os.path.join(root, f))
