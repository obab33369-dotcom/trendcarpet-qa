import os
import re

folder = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
if not os.path.exists(folder):
    print("Folder does not exist!")
    exit(1)

files = os.listdir(folder)
unique_products = set()
matta_files = []
for f in files:
    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        # Remove leading digits and underscore
        name = re.sub(r'^\d+_', '', f)
        # Get the first part before -
        parts = name.split('-')
        category = parts[0]
        unique_products.add(category)
        if "matta" in f.lower() or "rug" in f.lower() or "carpet" in f.lower():
            matta_files.append(f)

print("Total files:", len(files))
print("Categories present:", sorted(list(unique_products)))
print("Found matta/rug/carpet files count:", len(matta_files))
if matta_files:
    print("Some matta files:")
    for mf in matta_files[:10]:
        print(mf)
