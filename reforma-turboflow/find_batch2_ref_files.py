import os
import csv
import re

root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

def check_batch(batch_name, folder_name):
    csv_path = os.path.join(project_dir, f"turboflow_tracking_log_full_catalog_batch{batch_name}.csv")
    folder_path = os.path.join(root_dir, folder_name)
    
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return
        
    folder_files = {}
    for f in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, f)):
            base, ext = os.path.splitext(f.lower())
            folder_files[f.lower()] = f
            folder_files[base] = f
            
            # Normalize
            norm = re.sub(r'^\d+[_-]', '', base)
            norm = re.sub(r'-\d+-\w+-wonder$', '', norm)
            norm = re.sub(r'-\d+$', '', norm)
            folder_files[norm.lower()] = f
            
    required = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            refs = row.get("References Utilized", "")
            for r in refs.split(";"):
                r = r.strip()
                if r:
                    required.add(r)
                    
    mismatches = []
    for r in sorted(list(required)):
        r_lower = r.lower()
        r_base = os.path.splitext(r_lower)[0]
        
        if r_lower not in folder_files and r_base not in folder_files:
            norm_r = re.sub(r'^\d+[_-]', '', r_base)
            norm_r = re.sub(r'-\d+-\w+-wonder$', '', norm_r)
            norm_r = re.sub(r'-\d+$', '', norm_r)
            if norm_r.lower() not in folder_files:
                mismatches.append(r)
                
    print(f"Batch {batch_name} vs {folder_name}: {len(mismatches)} mismatches out of {len(required)} required.")
    for m in mismatches[:10]:
        print(f"  Missing: '{m}'")

check_batch("2a", "turboflow_batch2_produkter_aktiva_del1")
check_batch("2b", "turboflow_batch2_produkter_aktiva_del2")
