import os

search_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
print("Searching for pendant lamps...")

matches = []
for root, dirs, files in os.walk(search_dir):
    for f in files:
        if any(x in f.lower() for x in ['taklampa', 'pendel', 'oslo', 'adventstjarna']):
            if f.endswith('.jpg') and 'backup' not in root.lower() and 'ftp_upload' not in root.lower():
                matches.append(os.path.join(root, f))
                if len(matches) >= 15:
                    break
    if len(matches) >= 15:
        break

print(f"Found {len(matches)} matches:")
for m in matches:
    print(m)
