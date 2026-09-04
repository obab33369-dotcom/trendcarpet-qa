import json
import os

# Folders to check
folders = {
    "missed-products-upload": r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\missed-products-upload\artiklar",
    "temporary-ftp-upload": r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temporary-ftp-upload\artiklar",
    "chairs_cropped3": r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\chairs_cropped3\artiklar",
    "ftp_upload_cropped": r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped\artiklar"
}

# JSON files to check
json_files = [
    "rooms_turboflow.json",
    "rooms_turboflow_batch1.json",
    "rooms_turboflow_batch2.json",
    "rooms_turboflow_full_catalog.json",
    "turboflow_ready.json",
    "turboflow_ready_batch2.json",
    "turboflow_ready_full_catalog.json"
]

# Get list of files in each folder (lowercase, with extension removed)
folder_contents = {}
for fkey, path in folders.items():
    if os.path.exists(path):
        files_dict = {}
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                base, ext = os.path.splitext(f.lower())
                files_dict[base] = f
                # Also store with ext for direct matching
                files_dict[f.lower()] = f
        folder_contents[fkey] = files_dict
        print(f"Folder '{fkey}' has {len(files_dict)//2} files.")
    else:
        print(f"Folder '{fkey}' path does not exist.")

for jf in json_files:
    if os.path.exists(jf):
        with open(jf, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Failed to parse {jf}: {e}")
                continue
                
        print(f"\nChecking JSON: {jf} ({len(data)} rows)...")
        # Let's check which folders this JSON is meant for.
        # Since it can be any, let's find which folder has the highest match rate.
        for fkey, contents in folder_contents.items():
            missing_count = 0
            found_count = 0
            missing_examples = []
            
            for idx, row in enumerate(data):
                refs = [r.strip() for r in row.get("image_references", "").split(";") if r.strip()]
                for r in refs:
                    r_lower = r.lower()
                    r_base = os.path.splitext(r_lower)[0]
                    
                    # Check if r exists in contents
                    if r_lower in contents or r_base in contents:
                        found_count += 1
                    else:
                        missing_count += 1
                        if len(missing_examples) < 10:
                            missing_examples.append((idx + 1, r))
                            
            total_refs = found_count + missing_count
            if total_refs > 0:
                match_rate = found_count / total_refs * 100
                print(f"  vs Folder '{fkey}': Match Rate = {match_rate:.1f}% ({found_count}/{total_refs}). Missing: {missing_count}")
                if missing_count > 0 and match_rate > 5: # Only show examples if there is some matching
                    print("    Missing examples (Row #, reference name):")
                    for r_idx, ref in missing_examples:
                        print(f"      Row {r_idx}: '{ref}'")
            else:
                print(f"  vs Folder '{fkey}': No references found in JSON.")
