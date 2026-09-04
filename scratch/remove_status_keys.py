import json
import os

STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = json.load(f)
    
    keys_to_remove = ["zoom/1315_5.jpg", "zoom/1200180_3.jpg"]
    removed = []
    for key in keys_to_remove:
        if key in status_db:
            del status_db[key]
            removed.append(key)
            
    if removed:
        print(f"Removed keys {removed} from review_status.json.")
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_db, f, indent=2)
    else:
        print("No keys needed removal.")
else:
    print("Status file not found.")
