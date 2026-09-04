import os
import re

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    if not os.path.exists(TURBOFLOW_ROOT):
        print("Folder not found.")
        return
        
    print(f"Scanning files in {TURBOFLOW_ROOT}...")
    all_items = os.listdir(TURBOFLOW_ROOT)
    
    files = []
    for item in all_items:
        path = os.path.join(TURBOFLOW_ROOT, item)
        if os.path.isfile(path):
            files.append(item)
            
    print(f"Total files directly in root folder: {len(files)}")
    
    # Check naming conventions and ranges
    matching_files = []
    other_files = []
    
    # We want to parse the prefix index number from the files
    prefixes = []
    for f in files:
        m = re.match(r"^(\d+)", f)
        if m:
            prefix = int(m.group(1))
            prefixes.append(prefix)
            matching_files.append((prefix, f))
        else:
            other_files.append(f)
            
    print(f"Files starting with numbers: {len(matching_files)}")
    print(f"Other files in root: {len(other_files[:10])}")
    if len(other_files) > 10:
        print(f"  ... and {len(other_files) - 10} more non-numeric files.")
        
    if prefixes:
        prefixes = sorted(list(set(prefixes)))
        print(f"Prefix range found: {prefixes[0]} to {prefixes[-1]} (Unique prefixes: {len(prefixes)})")
        
        # Check first 5 and last 5 files in order
        matching_files.sort(key=lambda x: x[0])
        print("\nFirst 10 sorted files:")
        for prefix, fname in matching_files[:10]:
            print(f"  - {fname}")
            
        print("\nLast 10 sorted files:")
        for prefix, fname in matching_files[-10:]:
            print(f"  - {fname}")

if __name__ == "__main__":
    main()
