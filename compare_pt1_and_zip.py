import zipfile
import os

zip_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out-pt2.zip"
pt1_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out-pt1"

# Read all files in pt1
pt1_files = {}
for root, dirs, files in os.walk(pt1_dir):
    for f in files:
        rel_path = os.path.relpath(os.path.join(root, f), pt1_dir)
        # normalize path separators
        rel_path = rel_path.replace('\\', '/')
        pt1_files[rel_path] = os.path.getsize(os.path.join(root, f))

print(f"Total files in pt1 directory: {len(pt1_files)}")

# Read all files in zip
zip_files = {}
if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for info in zip_ref.infolist():
            if not info.is_dir():
                # zip path starts with 26-06-05-in-out/
                # let's map it to relative path by stripping the top directory
                parts = info.filename.split('/')
                if len(parts) > 1:
                    rel_path = '/'.join(parts[1:])
                    zip_files[rel_path] = info.file_size

print(f"Total files in zip: {len(zip_files)}")

# Compare keys
pt1_only = set(pt1_files.keys()) - set(zip_files.keys())
zip_only = set(zip_files.keys()) - set(pt1_files.keys())
both = set(pt1_files.keys()) & set(zip_files.keys())

print(f"Files only in pt1: {len(pt1_only)}")
print(f"Files only in zip: {len(zip_only)}")
print(f"Files in both: {len(both)}")

# Check if there are different file sizes in both
diff_sizes = []
for f in both:
    if pt1_files[f] != zip_files[f]:
        diff_sizes.append(f)

print(f"Files in both with different sizes: {len(diff_sizes)}")

# Print some of the zip only files if any
if zip_only:
    print("Example files only in zip:")
    for f in sorted(list(zip_only))[:20]:
        print(f"  {f} | Size: {zip_files[f]} bytes")
        
# Print some of the pt1 only files if any
if pt1_only:
    print("Example files only in pt1:")
    for f in sorted(list(pt1_only))[:20]:
        print(f"  {f} | Size: {pt1_files[f]} bytes")
