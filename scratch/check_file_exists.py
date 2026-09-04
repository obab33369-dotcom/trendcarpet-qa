import os

v3_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\artiklar"

files_to_check = [
    "19791-black-oak.jpg",
    "19791-ek.jpg",
    "19791-walnut.jpg",
    "19791-white-oak.jpg",
    "9971-oak.jpg"
]

for f in files_to_check:
    path = os.path.join(v3_dir, f)
    print(f"{f}: {os.path.exists(path)}")
