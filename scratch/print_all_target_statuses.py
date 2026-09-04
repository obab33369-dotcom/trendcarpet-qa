import json
import os

db_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected\review_status.json"
targets = [
    '19005-m', '19744-c', '19791-black-oak', '19791-ek', '19791-walnut',
    '19791-white-oak-grey', '19791-white-oak', '19791', '19798-grey',
    '2372-walnut', '9971-oak', 'adst-beige', 'adst-brown', 'adst-white',
    'alm-3065', 'ww-advent-star-white-2'
]

if os.path.exists(db_path):
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    print("Status of all target SKUs in the test database:")
    for key in sorted(db.keys()):
        fn = os.path.basename(key).lower()
        for t in targets:
            if fn.startswith(t + '.') or fn.startswith(t + '_'):
                print(f"  {key}: {db[key].get('status')} | Reason: {db[key].get('reason', '')}")
                break
else:
    print("Database not found.")
