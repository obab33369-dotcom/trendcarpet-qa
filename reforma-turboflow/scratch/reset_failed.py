import json

status_file = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

try:
    with open(status_file, "r", encoding="utf-8") as f:
        db = json.load(f)
except Exception as e:
    print(f"Error loading review_status.json: {e}")
    exit(1)

# Find keys with verification_failed status
failed_keys = [k for k, v in db.items() if v.get("status") == "verification_failed"]

print(f"Found {len(failed_keys)} failed entries to reset:")
for k in failed_keys:
    print(f" - {k}")

# Remove these keys
for k in failed_keys:
    del db[k]

# Save the updated DB back
with open(status_file, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print("Successfully reset entries in review_status.json!")
