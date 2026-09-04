import os
from PIL import Image
from datetime import datetime

dir_in_out = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out"
dir_pt1 = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out-pt1\Original"

def get_exif_date(filepath):
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        if exif:
            dstr = exif.get(36867) or exif.get(306)
            if dstr:
                return datetime.strptime(dstr, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        pass
    return None

# Load pt1 files metadata
pt1_dates = {}
pt1_sizes = {}
for root, dirs, files in os.walk(dir_pt1):
    folder_name = os.path.basename(root)
    if folder_name == "Original" or folder_name == "":
        continue
    for f in files:
        if f.lower().endswith(('.jpg', '.jpeg')):
            path = os.path.join(root, f)
            d = get_exif_date(path)
            if d:
                pt1_dates[d] = folder_name
            pt1_sizes[os.path.getsize(path)] = folder_name

# Load io files
io_files = sorted([f for f in os.listdir(dir_in_out) if f.lower().endswith(('.jpg', '.jpeg'))])
photos = []
for f in io_files:
    path = os.path.join(dir_in_out, f)
    d = get_exif_date(path)
    s = os.path.getsize(path)
    folder = None
    if d in pt1_dates:
        folder = pt1_dates[d]
    elif s in pt1_sizes:
        folder = pt1_sizes[s]
    photos.append({
        'name': f,
        'time': d,
        'size': s,
        'folder': folder
    })

# Output chronological list
prev_time = None
for i, p in enumerate(photos):
    gap_str = ""
    if prev_time and p['time']:
        gap = (p['time'] - prev_time).total_seconds()
        gap_str = f" (+{int(gap)}s)"
    prev_time = p['time']
    time_str = p['time'].strftime('%H:%M:%S') if p['time'] else "NO TIME"
    folder_str = f" -> {p['folder']}" if p['folder'] else " [UNMAPPED]"
    print(f"{p['name']} | {time_str}{gap_str:8s} | {folder_str}")
