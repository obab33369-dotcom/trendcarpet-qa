import json

status_file = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

try:
    with open(status_file, "r", encoding="utf-8") as f:
        db = json.load(f)
except Exception as e:
    print(f"Error loading review_status.json: {e}")
    exit(1)

failed_keys = [
    'artiklar/H000021092.jpg', 'artiklar/matgrupp17.jpg', 'artiklar/matgrupp23.jpg', 
    'artiklar/matgrupp26.jpg', 'artiklar/matgrupp28.jpg', 'artiklar/matgrupp30.jpg', 
    'artiklar/matgrupp33.jpg', 'artiklar/matgrupp36.jpg', 'artiklar/matgrupp39.jpg', 
    'artiklar/matgrupp51.jpg', 'artiklar/matgrupp6.jpg', 'artiklar/matgrupp7.jpg', 
    'artiklar/MG1505.jpg', 'artiklar/MLM-502390.jpg', 'artiklar/NOVASU02.jpg'
]

print("Check reset items:")
for k in failed_keys:
    val = db.get(k)
    if val:
        print(f" - {k}: status={val.get('status')} | reason={val.get('reason')} | category={val.get('category')} | timestamp={val.get('timestamp')}")
    else:
        print(f" - {k}: Not found in DB (unreviewed/processing)")

print(f"Total keys in DB: {len(db)}")
