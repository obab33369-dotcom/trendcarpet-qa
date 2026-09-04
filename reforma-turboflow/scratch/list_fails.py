import json

status_file = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

try:
    with open(status_file, "r", encoding="utf-8") as f:
        db = json.load(f)
except Exception as e:
    print(f"Error loading review_status.json: {e}")
    exit(1)

fails = [(k, v) for k, v in db.items() if v.get("status") == "verification_failed"]
print(f"Total verification failures: {len(fails)}")
for i, (k, v) in enumerate(fails):
    print(f"{i+1}. {k}")
    print(f"   Category: {v.get('category')}")
    print(f"   Reason: {v.get('reason')}")
    print(f"   Timestamp: {v.get('timestamp')}")
    print("-" * 50)
