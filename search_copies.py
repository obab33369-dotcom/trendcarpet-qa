import os

root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
target_names = ["B59A0001.JPG", "B59A0002.JPG", "B59A0003.JPG", "B59A0004.JPG", "B59A0005.JPG"]

found_by_name = []
found_b59a = []

for root, dirs, files in os.walk(root_dir):
    # skip some common system/cache folders if any
    for f in files:
        if f in target_names:
            found_by_name.append(os.path.join(root, f))
        if "B59A" in f:
            found_b59a.append(os.path.join(root, f))

print(f"Found targets by name ({len(found_by_name)}):")
for path in found_by_name:
    print("  ", path)

print(f"\nTotal B59A files found: {len(found_b59a)}")
# Let's see the directories of found B59A files
dirs_with_b59a = set(os.path.dirname(p) for p in found_b59a)
print("Directories containing B59A files:")
for d in sorted(list(dirs_with_b59a)):
    print("  ", d)
