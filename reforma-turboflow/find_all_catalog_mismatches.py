import os
import csv
import re

# Load all files in the active batch folders on OneDrive
root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
active_folders = [
    f for f in os.listdir(root_dir)
    if os.path.isdir(os.path.join(root_dir, f)) and ("produkter_aktiva" in f.lower() or "batch2_produkter" in f.lower())
]

onedrive_files = {}
for folder in active_folders:
    path = os.path.join(root_dir, folder)
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            base, ext = os.path.splitext(f.lower())
            # Map both base name and full name to the actual filename
            onedrive_files[base] = f
            onedrive_files[f.lower()] = f
            # Also map normalized name
            norm = re.sub(r'^\d+[_-]', '', base)
            norm = re.sub(r'-\d+-\w+-wonder$', '', norm)
            norm = re.sub(r'-\d+$', '', norm)
            onedrive_files[norm.lower()] = f

print(f"Loaded {len(onedrive_files)} lookup keys from OneDrive folders.")

csv_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\turboflow_ready_full_catalog.csv"
if not os.path.exists(csv_path):
    print("CSV file does not exist.")
else:
    mismatches = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            refs = [r.strip() for r in row.get("image_references", "").split(";") if r.strip()]
            for r in refs:
                r_lower = r.lower()
                r_base = os.path.splitext(r_lower)[0]
                if r_lower not in onedrive_files and r_base not in onedrive_files:
                    mismatches.add(r)
                    
    print(f"Found {len(mismatches)} unique missing references:")
    for m in sorted(list(mismatches))[:50]:
        print(f"  '{m}'")
