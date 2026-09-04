import json
import os

STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\review_status.json"

bad_images = [
    "010-natural.jpg", "100437.jpg", "100438.jpg", "100514.jpg", "102576.jpg",
    "1211-c.jpg", "15135-1.jpg", "2252-svart.jpg", "2300232.jpg", "45921.jpg",
    "85624.jpg", "88983.jpg", "91467.jpg", "91469.jpg", "91682.jpg", "93161.jpg",
    "alm-3061-t-25.jpg", "ct-175.jpg", "ct-186.jpg", "da-163.jpg", "eilens01-wood.jpg",
    "h000018252.jpg", "jn2005-004.jpg", "ks-01-m-silver.jpg", "ks-01-w-wood.jpg",
    "mobellass-large-gra.jpg", "puntwd01.jpg", "rh1905-13.jpg", "rh1905-14.jpg",
    "rh1905-17.jpg", "rh2012-39.jpg", "rh2012-40.jpg", "rh2012-42.jpg", "rw811.jpg",
    "ws-c1008.jpg", "ws-rt01a.jpg", "yd-g18-w.jpg"
]

if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = {k.lower(): v for k, v in json.load(f).items()}
        
    print(f"{'Filnamn':<25} | {'Status':<15} | {'Original BBox':<25} | {'BBox':<25}")
    print("-" * 100)
    for img in bad_images:
        db_key_main = f"artiklar/{img}".lower()
        if db_key_main in status_db:
            entry = status_db[db_key_main]
            status = entry.get("status")
            orig_bbox = entry.get("original_bbox")
            bbox = entry.get("bbox")
            print(f"{img:<25} | {str(status):<15} | {str(orig_bbox):<25} | {str(bbox):<25}")
        else:
            print(f"{img:<25} | Hittades inte i DB")
else:
    print(f"Hittade inte statusfilen: {STATUS_FILE}")
