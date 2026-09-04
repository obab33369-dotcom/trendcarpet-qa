import os
import re

dirs_to_search = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
]

targets = ["eilens", "mobellass"]

for target in targets:
    print(f"Söker efter {target}...")
    found = False
    for base_dir in dirs_to_search:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if target.lower() in f.lower():
                    print(f"  Hittade match: {os.path.join(root, f)}")
                    found = True
    if not found:
        print("  Ingen match hittades.")

