import json
import os

STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = json.load(f)
    
    key = "zoom/1200180_3.jpg"
    if key in status_db:
        del status_db[key]
        print(f"Removed key '{key}' from review_status.json.")
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_db, f, indent=2)
    else:
        print(f"Key '{key}' not found in review_status.json.")
else:
    print("Status file not found.")
