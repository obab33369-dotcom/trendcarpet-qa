import os
import fnmatch

search_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
pattern = "*2372-walnut*"
pattern_alt = "*2372_walnut*"

print("Searching for files on OneDrive...")
matches = []

for root, dirs, files in os.walk(search_dir):
    for filename in files:
        if fnmatch.fnmatch(filename.lower(), pattern) or fnmatch.fnmatch(filename.lower(), pattern_alt):
            full_path = os.path.join(root, filename)
            matches.append(full_path)

print(f"Found {len(matches)} matches:")
for m in matches:
    print(m)
