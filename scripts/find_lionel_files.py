import os

search_roots = [
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
]

found = []
for root_path in search_roots:
    if not os.path.exists(root_path): continue
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if "lionel" in file.lower() or "1100476" in file.lower():
                found.append(os.path.join(root, file))

print(f"Found {len(found)} Lionel chair files:")
for f in sorted(list(set(found))):
    print(f"  {f} -> Size: {os.path.getsize(f)} bytes")
