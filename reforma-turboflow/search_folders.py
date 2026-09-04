import os
import re

ORIG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]

keywords = ["angom", "montmartre", "midnatt", "oslo", "texas", "francisco", "hydra", "vintage"]

print("--- FOLDER SEARCH RESULTS ---")
for kw in keywords:
    print(f"\nKeyword: {kw}")
    for folder in orig_folders:
        # replace swedish chars
        folder_clean = folder.lower()
        repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u'}
        for char, rep in repl.items():
            folder_clean = folder_clean.replace(char, rep)
        if kw in folder_clean:
            print(f"  {folder}")
