import json
import os

status_file = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

if not os.path.exists(status_file):
    print("Status file not found.")
else:
    with open(status_file, 'r', encoding='utf-8') as f:
        db = json.load(f)
    print(f"Loaded status DB with {len(db)} entries.")
    
    skus_to_check = ['19791-ek', '9971-oak', '19005-m', '19744-c', '19791-walnut', '19791-white-oak']
    for key in sorted(db.keys()):
        # Check if any of our skus to check are in the key
        if any(sku in key.lower() for sku in skus_to_check):
            print(f"Key: {key}")
            print(f"  Value: {json.dumps(db[key], indent=2)}")
