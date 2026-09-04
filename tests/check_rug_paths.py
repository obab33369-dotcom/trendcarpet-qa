import json
import os

with open('pt1_gallery_metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

disk_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-08-27-Print-h-r-g-pt1-x"
for rug_name in meta['rugs'].keys():
    folder_on_disk = os.path.join(disk_dir, '1500px', rug_name)
    exists = os.path.exists(folder_on_disk)
    print(f"Rug: {repr(rug_name)} -> Exists on disk: {exists}")
