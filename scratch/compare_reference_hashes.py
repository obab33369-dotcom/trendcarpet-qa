import os
import hashlib

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

ref_name = "2021_matta-carrano-brun-vit.jpg"

def get_md5(path):
    if not os.path.exists(path):
        return None
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# Find the ref file on OneDrive first
ref_path = None
for root, dirs, files in os.walk(PICTURES_DIR):
    if ref_name in files:
        ref_path = os.path.join(root, ref_name)
        break

if not ref_path:
    print(f"Could not find reference file {ref_name} on OneDrive.")
    # Try alternate search
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        if ref_name in files:
            ref_path = os.path.join(root, ref_name)
            break

if ref_path:
    ref_md5 = get_md5(ref_path)
    ref_size = os.path.getsize(ref_path)
    print(f"Target Reference: {ref_name}")
    print(f"  Path: {ref_path}")
    print(f"  Size: {ref_size} bytes")
    print(f"  MD5 : {ref_md5}")
    
    # Scan reforma-original-images for matches
    orig_dir = os.path.join(WORKSPACE_DIR, "reforma-original-images")
    print(f"\nScanning {orig_dir} for matching MD5 or size...")
    
    md5_matches = []
    size_matches = []
    
    for f in os.listdir(orig_dir):
        path = os.path.join(orig_dir, f)
        if os.path.isfile(path) and f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            f_size = os.path.getsize(path)
            if f_size == ref_size:
                f_md5 = get_md5(path)
                if f_md5 == ref_md5:
                    md5_matches.append(f)
                else:
                    size_matches.append(f)
                    
    print("\nMatches by MD5 (Byte-for-byte identical):")
    for match in md5_matches:
        print(f"  - {match}")
        
    print("\nMatches by Size only (different content):")
    for match in size_matches[:10]:
        print(f"  - {match}")
else:
    print(f"Reference file {ref_name} not found anywhere.")
