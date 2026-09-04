import os
import hashlib

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# We need to find where these reference files are stored. Let's look for them.
# Usually, they might be in a references folder, or let's search where they exist.
# Let's find where files ending in "matta-seronis-svart-beige.jpg" or "matta-orlisse-brun.png" are located in the workspace or OneDrive.

paths_to_check = []
for root, dirs, files in os.walk(WORKSPACE_DIR):
    for f in files:
        if "seronis" in f.lower() or "orlisse" in f.lower() or "aravelle" in f.lower() or "sorvento" in f.lower():
            paths_to_check.append(os.path.join(root, f))

for root, dirs, files in os.walk(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"):
    for f in files:
        if "seronis" in f.lower() or "orlisse" in f.lower() or "aravelle" in f.lower() or "sorvento" in f.lower():
            if "Reforma-Full-Catalog-sortering" not in root: # Skip the target sorted dirs to avoid spam
                paths_to_check.append(os.path.join(root, f))

# Let's group by filename and print size + md5
print(f"Found {len(paths_to_check)} candidate reference/image files. Analyzing distinct ones...")

results = {}
for p in paths_to_check:
    name = os.path.basename(p)
    if "00_REFERENCE_" in name:
        continue
    try:
        size = os.path.getsize(p)
        with open(p, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        results[name] = (size, md5, p)
    except Exception:
        pass

for name, (size, md5, p) in sorted(results.items()):
    print(f"File: {name}")
    print(f"  Size: {size} bytes | MD5: {md5}")
    print(f"  Path: {p}")
    print("-" * 50)
