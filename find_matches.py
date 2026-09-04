import os
import hashlib
from PIL import Image

dir_in_out = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out"
dir_pt1 = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out-pt1"

# Gather files from dir_in_out
in_out_files = {}
for filename in os.listdir(dir_in_out):
    filepath = os.path.join(dir_in_out, filename)
    if os.path.isfile(filepath):
        size = os.path.getsize(filepath)
        in_out_files[filename] = {
            'path': filepath,
            'size': size
        }

print(f"Found {len(in_out_files)} files in 26-06-05-in-out")

# Gather files from dir_pt1 (under Original)
pt1_original_dir = os.path.join(dir_pt1, "Original")
pt1_files = {}
if os.path.exists(pt1_original_dir):
    for root, dirs, files in os.walk(pt1_original_dir):
        folder_name = os.path.basename(root)
        if folder_name == "Original":
            continue
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            pt1_files[file] = {
                'path': filepath,
                'folder': folder_name,
                'size': size
            }
print(f"Found {len(pt1_files)} files in pt1/Original across {len(os.listdir(pt1_original_dir))} folders")

# Try to match by size
size_matches = {}
for pt1_name, pt1_info in pt1_files.items():
    pt1_size = pt1_info['size']
    matches = []
    for io_name, io_info in in_out_files.items():
        if abs(io_info['size'] - pt1_size) < 1024:  # within 1KB
            matches.append(io_name)
    if matches:
        size_matches[pt1_name] = matches

print(f"Matched {len(size_matches)} out of {len(pt1_files)} pt1 files by size")
if size_matches:
    print("Example matches:")
    for pt1_name, matches in list(size_matches.items())[:10]:
        print(f"  {pt1_name} -> {matches} in folder {pt1_files[pt1_name]['folder']}")

# Let's check EXIF data (DateTimeOriginal) of the files to see if we can match them perfectly
def get_exif_date(filepath):
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        if exif:
            # 36867 is DateTimeOriginal
            return exif.get(36867) or exif.get(306)
    except Exception as e:
        pass
    return None

# Check EXIF dates of some files in in_out
io_dates = {}
for name, info in in_out_files.items():
    if name.lower().endswith(('.jpg', '.jpeg')):
        date = get_exif_date(info['path'])
        if date:
            io_dates[name] = date

print(f"Found EXIF dates for {len(io_dates)} files in 26-06-05-in-out")

pt1_dates = {}
for name, info in pt1_files.items():
    if name.lower().endswith(('.jpg', '.jpeg')):
        date = get_exif_date(info['path'])
        if date:
            pt1_dates[name] = date
print(f"Found EXIF dates for {len(pt1_dates)} files in pt1/Original")

# Match by EXIF date
exif_matches = {}
for pt1_name, date in pt1_dates.items():
    matches = [io_name for io_name, io_date in io_dates.items() if io_date == date]
    if matches:
        exif_matches[pt1_name] = matches

print(f"Matched {len(exif_matches)} files by EXIF date")
if exif_matches:
    print("Example EXIF matches:")
    for pt1_name, matches in list(exif_matches.items())[:10]:
        print(f"  {pt1_name} -> {matches} in folder {pt1_files[pt1_name]['folder']}")
