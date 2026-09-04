import json

status_file = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

try:
    with open(status_file, "r", encoding="utf-8") as f:
        db = json.load(f)
except Exception as e:
    print(f"Error loading review_status.json: {e}")
    exit(1)

print("Recent updates (since 14:28 today):")
count = 0
for k, v in db.items():
    ts = v.get("timestamp", "")
    if ts >= "2026-06-09 14:28":
        print(f" - {k}: status={v.get('status')} | reason={v.get('reason')} | ts={ts}")
        count += 1
print(f"Total updated: {count}")
