import os
from PIL import Image
from collections import defaultdict

dir_in_out = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out"
dir_pt1 = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out-pt1\Original"

def get_exif_date(filepath):
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        if exif:
            # 36867 is DateTimeOriginal, 306 is DateTime
            return exif.get(36867) or exif.get(306)
    except Exception as e:
        pass
    return None

# List all original files
io_files = sorted([f for f in os.listdir(dir_in_out) if f.lower().endswith(('.jpg', '.jpeg'))])

# Load EXIF dates for io files
io_dates = {}
io_sizes = {}
for f in io_files:
    path = os.path.join(dir_in_out, f)
    io_dates[f] = get_exif_date(path)
    io_sizes[f] = os.path.getsize(path)

# Load pt1 files
pt1_files_by_folder = defaultdict(list)
for root, dirs, files in os.walk(dir_pt1):
    folder_name = os.path.basename(root)
    if folder_name == "Original" or folder_name == "":
        continue
    for f in files:
        if f.lower().endswith(('.jpg', '.jpeg')):
            path = os.path.join(root, f)
            pt1_files_by_folder[folder_name].append({
                'name': f,
                'path': path,
                'date': get_exif_date(path),
                'size': os.path.getsize(path)
            })

# Map each io file to a folder
io_to_folder = {}
for f in io_files:
    io_date = io_dates[f]
    io_size = io_sizes[f]
    matched_folders = set()
    
    # Check date matches
    if io_date:
        for folder, p_list in pt1_files_by_folder.items():
            for p in p_list:
                if p['date'] == io_date:
                    matched_folders.add(folder)
                    
    # Check size matches (fallback)
    for folder, p_list in pt1_files_by_folder.items():
        for p in p_list:
            if p['size'] == io_size:
                matched_folders.add(folder)
                
    if matched_folders:
        io_to_folder[f] = list(matched_folders)
    else:
        io_to_folder[f] = ["UNMAPPED"]

# Let's write a file summary.txt in REFORMA to see the complete list
with open("summary.txt", "w") as out:
    out.write("FILE MAPPING SUMMARY:\n")
    for f in io_files:
        out.write(f"{f} | Date: {io_dates[f]} | Size: {io_sizes[f]} | Mapped to: {io_to_folder[f]}\n")

print("Saved detailed mapping to summary.txt")

# Let's print the folder details: which files belong to which folder based on the mapping
print("\n--- Folder to Original Files mapping ---")
folder_to_io_files = defaultdict(list)
for f, folders in io_to_folder.items():
    for folder in folders:
        folder_to_io_files[folder].append(f)

for folder, files in sorted(folder_to_io_files.items()):
    if folder == "UNMAPPED":
        continue
    print(f"Folder: {folder}")
    print(f"  Mapped original files ({len(files)}): {files[0]} to {files[-1]} (Total list: {files})")
    
# Let's look at the UNMAPPED files. We want to see where they fit chronologically!
# They might be gaps in the sequence. Let's see the sequence of all files and their mappings.
print("\n--- Chronological sequence of files and their mapped folders ---")
current_folder = None
current_group = []
for f in io_files:
    folders = io_to_folder[f]
    folder_str = ", ".join(folders)
    if folder_str != current_folder:
        if current_folder is not None:
            print(f"  {current_group[0]} - {current_group[-1]} ({len(current_group)} files) -> {current_folder}")
        current_folder = folder_str
        current_group = [f]
    else:
        current_group.append(f)
if current_group:
    print(f"  {current_group[0]} - {current_group[-1]} ({len(current_group)} files) -> {current_folder}")
