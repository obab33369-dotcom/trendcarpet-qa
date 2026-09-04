import os
import hashlib

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
topaz_dir = os.path.join(PICTURES_DIR, "TEST TOPAZ")
orig_dir = os.path.join(WORKSPACE_DIR, "reforma-original-images")

targets = [
    "2008_matta-aravelle-turkos-multi.jpg",
    "2011_matta-arvella-rod-gron.jpg",
    "2012_matta-aureline-beige-brun.jpg",
    "2013_matta-aureline-beige-gra.jpg",
    "2014_matta-aureline-gron.jpg",
    "2016_matta-avendo-rod.jpg",
    "2017_matta-belden-gron.jpg",
    "2020_matta-calvera-rod.jpg",
    "2021_matta-carrano-brun-vit.jpg",
    "2087_matta-seronis-svart-beige.jpg",
    "2089_matta-sorvento-svart-beige.jpg",
    "2104_matta-velenna-svart-beige.jpg"
]

def get_md5(path):
    if not os.path.exists(path):
        return None
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

print("Checking MD5 hashes of all 12 carpet reference files against reforma-original-images:")

orig_hashes = {}
if os.path.exists(orig_dir):
    for f in os.listdir(orig_dir):
        path = os.path.join(orig_dir, f)
        if os.path.isfile(path) and f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            orig_hashes[get_md5(path)] = f

for ref_name in targets:
    path = os.path.join(topaz_dir, ref_name)
    if not os.path.exists(path):
        print(f"Ref: {ref_name} -> File NOT found in TEST TOPAZ!")
        continue
    
    md5 = get_md5(path)
    match = orig_hashes.get(md5, "NO MATCH")
    print(f"Ref: {ref_name}")
    print(f"  MD5  : {md5}")
    print(f"  Match: {match}")
    print("-" * 60)
