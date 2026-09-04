import os

paths_to_check = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full"
]

print("Checking directories for SKUs...")
for base_dir in paths_to_check:
    if not os.path.exists(base_dir):
        print(f"Dir not found: {base_dir}")
        continue
    print(f"\nScanning: {base_dir}")
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if any(x in f for x in ['19791', '9971', '19744', '19005']):
                print(f"  Found: {os.path.join(root, f)}")
