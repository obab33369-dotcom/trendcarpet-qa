import json
import os
import re
from PIL import Image

REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
STATUS_FILE = os.path.join(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2", "review_status.json")

# Source image
src_image = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\cabinet\White background\TV-bänk _Grant_ - EkJärn\TV-bänk _Grant_ - EkJärn-01-W-wonder.jpg"

if os.path.exists(src_image):
    with Image.open(src_image) as img:
        print(f"Source Image: {src_image}")
        print(f"Size: {img.size}")
else:
    print("Source image not found!")

# Let's search for 9971-oak in status_db
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
    for k, v in db.items():
        if "9971-oak" in k:
            print(f"Key: {k}")
            print(json.dumps(v, indent=2))
