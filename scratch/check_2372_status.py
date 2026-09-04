import json
import os

db_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected\review_status.json"

if os.path.exists(db_path):
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    print("Entries for 2372-walnut:")
    for k, v in sorted(db.items()):
        if "2372-walnut" in k:
            print(f"{k}:")
            print(json.dumps(v, indent=2))
else:
    print("No DB found")
