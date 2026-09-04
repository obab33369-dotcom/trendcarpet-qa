import os

v3_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\artiklar"
files = sorted([f for f in os.listdir(v3_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

target_file = "99070.jpg"
if target_file in files:
    idx = files.index(target_file)
    grid_num = (idx // 25) + 1
    cell_num = idx % 25
    print(f"File {target_file} is in grid_{grid_num}.jpg at cell {cell_num} (index {idx})")
else:
    print(f"File {target_file} not found in the list of files.")
