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

# Define the actual rug blocks based on our analysis
rug_blocks = [
    {"name": "Ragusa (svart/creme) - SAKNAS", "start": "B59A0001.JPG", "end": "B59A0012.JPG", "mapped": False},
    {"name": "Dhamar (grön)", "start": "B59A0013.JPG", "end": "B59A0024.JPG", "mapped": True},
    {"name": "Mekele (taupe)", "start": "B59A0028.JPG", "end": "B59A0039.JPG", "mapped": True},
    {"name": "Devon (brun)", "start": "B59A0047.JPG", "end": "B59A0061.JPG", "mapped": True},
    {"name": "Tracino (taupe)", "start": "B59A0065.JPG", "end": "B59A0078.JPG", "mapped": True},
    {"name": "Ragusa (taupe/creme)", "start": "B59A0083.JPG", "end": "B59A0095.JPG", "mapped": True},
    {"name": "Cordoba (taupe)", "start": "B59A0098.JPG", "end": "B59A0111.JPG", "mapped": True},
    {"name": "Mekele (brun)", "start": "B59A0115.JPG", "end": "B59A0128.JPG", "mapped": True},
    {"name": "Djerba (brun)", "start": "B59A0132.JPG", "end": "B59A0146.JPG", "mapped": True},
    {"name": "Nicosia (brun)", "start": "B59A0149.JPG", "end": "B59A0162.JPG", "mapped": True},
    {"name": "Sousse (taupe)", "start": "B59A0165.JPG", "end": "B59A0182.JPG", "mapped": True},
    {"name": "Färg-/gråkort (referens)", "start": "B59A0183.JPG", "end": "B59A0183.JPG", "mapped": False}
]

print("| Matta | Bildintervall | Antal bilder | Status |")
print("| :--- | :--- | :---: | :--- |")
for block in rug_blocks:
    # count files in interval
    start_num = int(block["start"].split("B59A")[1].split(".JPG")[0])
    end_num = int(block["end"].split("B59A")[1].split(".JPG")[0])
    count = end_num - start_num + 1
    status_str = "Finns i pt1" if block["mapped"] else ("**SAKNAS** (Finns ej i pt1)" if "SAKNAS" in block["name"] else "Referensbild")
    print(f"| {block['name'].split(' - ')[0]} | `{block['start']}` till `{block['end']}` | {count} | {status_str} |")
