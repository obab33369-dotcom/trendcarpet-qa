import hashlib
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def get_hash(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

rg01_6_path = os.path.join(WORKSPACE_DIR, "reforma-original-images", "RG01-6.jpg")
rg01_64_path = os.path.join(WORKSPACE_DIR, "reforma-original-images", "RG01-64.jpg")

print(f"RG01-6 (Velenna) hash: {get_hash(rg01_6_path)}")
print(f"RG01-64 (Arvella) hash: {get_hash(rg01_64_path)}")

# Search for other files with RG01-6's hash
target_hash = get_hash(rg01_6_path)
print(f"\nSearching for other files with hash {target_hash}...")
for root, dirs, files in os.walk(WORKSPACE_DIR):
    for f in files:
        if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            path = os.path.join(root, f)
            if get_hash(path) == target_hash:
                print(f"Found match: {path}")
