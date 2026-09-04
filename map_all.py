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

# Get all in-out photos with their EXIF date
in_out_photos = []
for filename in sorted(os.listdir(dir_in_out)):
    filepath = os.path.join(dir_in_out, filename)
    if os.path.isfile(filepath) and filename.lower().endswith(('.jpg', '.jpeg')):
        date = get_exif_date(filepath)
        size = os.path.getsize(filepath)
        in_out_photos.append({
            'name': filename,
            'path': filepath,
            'date': date,
            'size': size
        })

print(f"Total photos in in-out: {len(in_out_photos)}")

# Get all pt1 photos with their folder and EXIF date
pt1_photos = []
for root, dirs, files in os.walk(dir_pt1):
    folder_name = os.path.basename(root)
    if folder_name == "Original":
        continue
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg')):
            filepath = os.path.join(root, file)
            date = get_exif_date(filepath)
            size = os.path.getsize(filepath)
            pt1_photos.append({
                'name': file,
                'folder': folder_name,
                'path': filepath,
                'date': date,
                'size': size
            })

print(f"Total photos in pt1/Original: {len(pt1_photos)}")

# Group pt1 photos by their EXIF date
pt1_by_date = defaultdict(list)
for p in pt1_photos:
    if p['date']:
        pt1_by_date[p['date']].append(p)

# Also let's try to match by name if possible, or by size
# Let's map each photo in in-out to where it is used in pt1
mapping = []
for io in in_out_photos:
    matched_in_pt1 = []
    
    # 1. Match by EXIF date
    if io['date'] and io['date'] in pt1_by_date:
        matched_in_pt1 = pt1_by_date[io['date']]
    
    # If no match by date, let's see if we can match by size
    if not matched_in_pt1:
        # Check if there is any file in pt1 with exactly the same size
        for p in pt1_photos:
            if p['size'] == io['size']:
                matched_in_pt1.append(p)
                
    mapping.append({
        'io': io,
        'matched': matched_in_pt1
    })

# Output results
used_original_files = set()
unused_original_files = []

for m in mapping:
    io = m['io']
    matched = m['matched']
    if matched:
        used_original_files.add(io['name'])
    else:
        unused_original_files.append(io)

print(f"Used original files: {len(used_original_files)}")
print(f"Unused original files: {len(unused_original_files)}")
print("Unused files:")
for u in unused_original_files:
    print(f"  {u['name']} (Date: {u['date']}, Size: {u['size']})")

# Let's look at the sequence of photos in in-out, and display which folder they map to
print("\nPhoto sequence in 26-06-05-in-out and mapped folders in pt1:")
for m in mapping:
    io = m['io']
    matched = m['matched']
    folders = sorted(list(set(p['folder'] for p in matched))) if matched else ["UNMAPPED"]
    print(f"  {io['name']} | Date: {io['date']} | Folders: {folders}")
