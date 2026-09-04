import json
import os

STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2\review_status.json"

targets = [
    '19005-m', '19744-c', '19791-black-oak', '19791-ek', '19791-walnut',
    '19791-white-oak-grey', '19791-white-oak', '19791', '19798-grey',
    '2372-walnut', '9971-oak', 'adst-beige', 'adst-brown', 'adst-white',
    'alm-3065', 'ww-advent-star-white-2'
]

if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    print("=== TARGET SKU STATUS ===")
    for key, val in sorted(db.items()):
        # Check if key contains any of our targets
        fn = os.path.basename(key).lower()
        matched = False
        for t in targets:
            if fn.startswith(t + '.') or fn.startswith(t + '_'):
                matched = True
                break
        if matched:
            print(f"{key}:")
            print(json.dumps(val, indent=2))
            print("-" * 40)
else:
    print("Status file not found!")
