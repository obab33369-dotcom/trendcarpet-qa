import json
import os
from PIL import Image

STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2\review_status.json"
TEST_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2\artiklar"

if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    for k, v in db.items():
        if "19791" in k and "artiklar" in k:
            img_path = os.path.join(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2", k)
            if os.path.exists(img_path):
                with Image.open(img_path) as img:
                    print(f"Key: {k}")
                    print(f"Size: {img.size}")
                    print(json.dumps(v, indent=2))
                    print("-" * 50)
