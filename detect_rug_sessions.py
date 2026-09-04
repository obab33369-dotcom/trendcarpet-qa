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

# Let's detect sessions using a simple gap threshold.
# We will experiment with different gap thresholds (e.g. 90s, 120s, 150s, 180s)
for threshold in [90, 120, 150, 180]:
    print(f"\n--- SESSIONS WITH THRESHOLD = {threshold} SECONDS ---")
    sessions = []
    current = []
    for p in photos:
        if not current:
            current.append(p)
        else:
            prev = current[-1]
            gap = None
            if p['time'] and prev['time']:
                gap = (p['time'] - prev['time']).total_seconds()
            
            if gap is not None and gap > threshold:
                sessions.append(current)
                current = [p]
            else:
                current.append(p)
    if current:
        sessions.append(current)
        
    print(f"Total sessions: {len(sessions)}")
    for idx, sess in enumerate(sessions):
        first = sess[0]
        last = sess[-1]
        folders = sorted(list(set(p['folder'] for p in sess if p['folder'])))
        folder_str = ", ".join(folders) if folders else "UNMAPPED"
        time_str = first['time'].strftime('%H:%M:%S') if first['time'] else "NO TIME"
        print(f"Sess {idx+1:2d} | {first['name']} - {last['name']} | Count: {len(sess):2d} | Start: {time_str} | Folder: {folder_str}")
