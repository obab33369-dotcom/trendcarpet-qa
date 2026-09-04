import os
import json

BAD_CROPS_FILE = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\bad_crops_report.json"
STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\review_status.json"
ARTIKLAR_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\artiklar"

if not os.path.exists(BAD_CROPS_FILE):
    print("No bad crops report found!")
    exit(1)

with open(BAD_CROPS_FILE, 'r', encoding='utf-8') as f:
    bad_crops = json.load(f)

status_db = {}
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = {k.lower(): v for k, v in json.load(f).items()}

print(f"Loaded {len(bad_crops)} bad crop filenames from report.")
print(f"Loaded {len(status_db)} status entries.")

print("\n--- Status of flagged bad crops ---")
missing_on_disk = 0
found_on_disk = 0
status_counts = {}

for item in bad_crops:
    filename = item.get("filename")
    if not filename:
        continue
    
    # Determine slot and sku
    fn_lower = filename.lower()
    is_zoom = "_" in fn_lower and not fn_lower.endswith("_s.jpg")
    
    if is_zoom:
        db_key = f"zoom/{filename}".lower()
        disk_path = os.path.join(ARTIKLAR_DIR, "zoom", filename)
    elif fn_lower.endswith("_s.jpg"):
        db_key = f"artiklar/liten/{filename}".lower() # wait, status key might be different
        disk_path = os.path.join(ARTIKLAR_DIR, "liten", filename)
    else:
        db_key = f"artiklar/{filename}".lower()
        disk_path = os.path.join(ARTIKLAR_DIR, filename)
        
    status_entry = status_db.get(db_key, {})
    status = status_entry.get("status", "NOT_FOUND_IN_DB")
    
    exists = os.path.exists(disk_path)
    if exists:
        found_on_disk += 1
    else:
        missing_on_disk += 1
        
    status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"File: {filename} | Exists: {exists} | DB Status: {status} | Reason: {item.get('reason')}")

print("\nSummary:")
print(f"  Total: {len(bad_crops)}")
print(f"  Exists on disk: {found_on_disk}")
print(f"  Missing on disk: {missing_on_disk}")
print("  Status counts in DB:")
for s, count in status_counts.items():
    print(f"    - {s}: {count}")
