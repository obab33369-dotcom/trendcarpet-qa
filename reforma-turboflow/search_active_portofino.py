import os

search_keywords = ["t8049", "portofino"]
root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

active_folders = [
    f for f in os.listdir(root_dir)
    if os.path.isdir(os.path.join(root_dir, f)) and "produkter_aktiva" in f.lower()
]

for folder in active_folders:
    folder_path = os.path.join(root_dir, folder)
    for f in os.listdir(folder_path):
        if any(kw in f.lower() for kw in search_keywords):
            print(f"FOUND in {folder}: {f}")
