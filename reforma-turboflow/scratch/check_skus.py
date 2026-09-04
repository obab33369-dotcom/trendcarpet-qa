import json

status_file = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"

try:
    with open(status_file, "r", encoding="utf-8") as f:
        db = json.load(f)
except Exception as e:
    print(f"Error loading review_status.json: {e}")
    exit(1)

test_skus = ["0000104589", "102088", "102460", "1400034", "1400040"]

print("Status in DB for target SKUs:")
for k, v in db.items():
    sku = k.split("/")[-1].split("_")[0].split(".")[0]
    if sku in test_skus:
        print(f" - {k}: status={v.get('status')} | reason={v.get('reason')} | category={v.get('category')} | timestamp={v.get('timestamp')}")
