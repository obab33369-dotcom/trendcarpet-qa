import os
import hashlib

def get_md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

search_roots = [
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
]

print("=== SCANNING FOR VENTARO GRON GUL FILES ===")
found_files = []
for root in search_roots:
    for r, ds, fs in os.walk(root):
        for f in fs:
            if 'matta-ventaro-gron-gul' in f.lower() or '2111_matta-ventaro' in f.lower():
                full_path = os.path.join(r, f)
                size = os.path.getsize(full_path)
                md5 = get_md5(full_path)
                print(f"Path: {full_path}")
                print(f"  Size: {size} bytes | MD5: {md5}")
                found_files.append((full_path, size, md5))
                print("-" * 50)
