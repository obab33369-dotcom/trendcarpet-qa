import os

search_keyword = "hydra"
root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload"

for root, dirs, files in os.walk(root_dir):
    for f in files:
        if search_keyword in f.lower():
            print(f"FOUND: {os.path.join(root, f)}")
