import os
from PIL import Image
from datetime import datetime, timedelta

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

# Group photos into sessions.
# A new session starts if:
# - There is a gap > 120 seconds between consecutive photos AND at least one of the photos changes its folder status
# - Or there's a gap > 300 seconds (5 minutes) regardless
# Let's write a robust logic to group photos.
sessions = []
current_session = []

for p in photos:
    if not current_session:
        current_session.append(p)
    else:
        prev = current_session[-1]
        gap = None
        if p['time'] and prev['time']:
            gap = (p['time'] - prev['time']).total_seconds()
        
        # Determine if we should split
        split = False
        if gap is not None:
            if gap > 300:  # 5 minutes gap is always a new session
                split = True
            elif gap > 60:  # 1 minute gap is a split if the folder mapping changes
                prev_folder = prev['folder']
                curr_folder = p['folder']
                if prev_folder != curr_folder:
                    split = True
        else:
            split = True
            
        if split:
            sessions.append(current_session)
            current_session = [p]
        else:
            current_session.append(p)

if current_session:
    sessions.append(current_session)

print(f"Detected {len(sessions)} sessions:")
for i, sess in enumerate(sessions):
    first = sess[0]
    last = sess[-1]
    folders = list(set(p['folder'] for p in sess if p['folder']))
    folder_str = folders[0] if folders else "UNMAPPED"
    time_str = first['time'].strftime('%H:%M:%S') if first['time'] else "NO TIME"
    duration = ""
    if first['time'] and last['time']:
        dur_secs = (last['time'] - first['time']).total_seconds()
        duration = f" ({int(dur_secs)}s)"
    print(f"Session {i+1:2d} | {first['name']} to {last['name']} | Count: {len(sess):2d} | Start: {time_str}{duration} | Folder: {folder_str}")
