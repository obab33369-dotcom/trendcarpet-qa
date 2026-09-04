import json
import glob
import os
import csv
import re
import urllib.request
import time

project_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
download_dir = os.path.join(project_dir, "downloaded_missing_images")
os.makedirs(download_dir, exist_ok=True)

print("Gathering required images...")
required_images = set()
for csv_file in glob.glob(os.path.join(project_dir, "turboflow_tracking_log_full_catalog_batch*.csv")):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            refs = row.get('References Utilized', '')
            for ref in refs.split(';'):
                ref = ref.strip()
                if ref: required_images.add(ref)

print("Building index of existing images...")
image_index = {}
search_dirs = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ",
    r"C:\Users\AndronikLindgren\reforma_automation\reforma_arkiv",
    os.path.join(project_dir, "test_furniture"),
    os.path.join(project_dir, "new_rugs"),
    os.path.join(project_dir, "test_rugs")
]
onedrive_pictures_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
if os.path.exists(onedrive_pictures_dir):
    for entry in os.listdir(onedrive_pictures_dir):
        if entry.lower().startswith('turboflow_batch'):
            search_dirs.append(os.path.join(onedrive_pictures_dir, entry))

for sd in search_dirs:
    if os.path.exists(sd):
        for r, d, files in os.walk(sd):
            if 'batch' in r.lower() and '_images' in r.lower(): continue
            for f in files:
                if f.endswith(('.png', '.webp', '.jpg', '.jpeg')):
                    image_index[f.lower()] = os.path.join(r, f)

def normalize(s):
    s = s.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e'}
    for c, r in repl.items(): s = s.replace(c, r)
    s = re.sub(r'^\d+[_-]', '', s)
    s = re.sub(r'\.(jpg|jpeg|png|webp)$', '', s)
    s = re.sub(r'[^a-z0-9]', '', s)
    s = re.sub(r'(26uwonder|wonder|26u)$', '', s)
    return s

missing = []
print("Finding missing images...")
for img in required_images:
    match_src = None
    if img.lower() in image_index: match_src = True
    elif img.lower() + '.png' in image_index: match_src = True
    elif img.lower() + '.webp' in image_index: match_src = True
    elif img.lower() + '.jpg' in image_index: match_src = True
    if not match_src:
        norm_img = normalize(img)
        for k in image_index:
            norm_k = normalize(k)
            if norm_img == norm_k or norm_k.startswith(norm_img) or norm_img.startswith(norm_k):
                match_src = True
                break
    if not match_src:
        missing.append(img)

print(f"Total missing locally: {len(missing)}")

db = json.load(open(os.path.join(project_dir, 'brand_sku_dict.json'), encoding='utf-8'))
db_slugs = {k.lower(): v for k, v in db.items()}

# Pre-compute end-of-url map
url_map = {}
for k, v in db.items():
    u = v.get('url', '')
    if u:
        slug_from_url = u.rstrip('/').split('/')[-1].lower()
        url_map[slug_from_url] = v

success_count = 0
for m in missing:
    m_lower = m.lower()
    item_info = None
    if m_lower in db_slugs:
        item_info = db_slugs[m_lower]
    elif m_lower in url_map:
        item_info = url_map[m_lower]
    else:
        # try matching end of url
        for k, v in db.items():
            if v.get('url', '').endswith('/' + m_lower):
                item_info = v
                break

    if item_info and item_info.get('image_path'):
        image_path = item_info['image_path']
        # Reforma images are at https://www.reformasthlm.se + image_path
        # But wait, image_path could be just a relative path.
        if image_path.startswith('/'):
            remote_url = "https://www.reformasthlm.se" + image_path
        else:
            remote_url = "https://www.reformasthlm.se/" + image_path
        
        # We need to quote the URL properly as it may contain spaces
        from urllib.parse import urlsplit, urlunsplit, quote
        parts = list(urlsplit(remote_url))
        parts[2] = quote(parts[2])
        remote_url = urlunsplit(parts)

        # Output filename should exactly match what turboflow needs
        out_path = os.path.join(download_dir, m + ".jpg")
        
        if os.path.exists(out_path):
            success_count += 1
            continue

        try:
            req = urllib.request.Request(remote_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(out_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Downloaded: {m}")
            success_count += 1
            time.sleep(0.1)  # small delay to be polite
        except Exception as e:
            print(f"Failed to download {remote_url} for {m}: {e}")
    else:
        print(f"Could not find URL for: {m}")

print(f"Successfully downloaded {success_count} out of {len(missing)} missing images.")
