import os

search_roots = [
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
]

patterns = ["4100081", "4100071", "4100072", "1400041", "1400040", "3200459", "3100237", "1100476"]

found_files = []
for root_path in search_roots:
    if not os.path.exists(root_path):
        continue
    print(f"Searching in: {root_path}")
    for root, dirs, files in os.walk(root_path):
        for file in files:
            for pat in patterns:
                if pat in file:
                    path = os.path.join(root, file)
                    found_files.append((pat, path))

print(f"\nFound {len(found_files)} matching files:")
for pat, path in found_files:
    print(f"Pattern: {pat} -> Path: {path} -> Size: {os.path.getsize(path)} bytes")
