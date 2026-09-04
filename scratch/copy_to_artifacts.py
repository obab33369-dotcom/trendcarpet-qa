import os
import shutil

src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2\artiklar"
dest_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\9a89adb6-c2a2-4ca2-a186-3ca3c4d5681e"

files_to_copy = [
    ("19791-ek.jpg", "test_19791_ek.jpg"),
    ("19791.jpg", "test_19791_natur.jpg"),
    ("2372-walnut.jpg", "test_2372_walnut.jpg"),
    ("9971-oak.jpg", "test_9971_oak.jpg")
]

for src_name, dest_name in files_to_copy:
    src_path = os.path.join(src_dir, src_name)
    dest_path = os.path.join(dest_dir, dest_name)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"Copied {src_name} to {dest_name}")
    else:
        print(f"File not found: {src_name}")
