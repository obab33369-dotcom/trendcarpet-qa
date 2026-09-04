import os

search_keywords = ["t8049", "portofino"]
root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

for root, dirs, files in os.walk(root_dir):
    for f in files:
        if any(kw in f.lower() for kw in search_keywords):
            print(f"FOUND: {os.path.join(root, f)}")
