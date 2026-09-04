import os
import re
import datetime

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    if not os.path.exists(TURBOFLOW_ROOT):
        print(f"Directory not found: {TURBOFLOW_ROOT}")
        return
        
    print(f"Scanning directory: {TURBOFLOW_ROOT}...")
    
    files = []
    for f in os.listdir(TURBOFLOW_ROOT):
        path = os.path.join(TURBOFLOW_ROOT, f)
        if not os.path.isfile(path):
            continue
            
        m = re.match(r"^(\d+)-architectural-digest-styl-(\d+)\.png$", f)
        if m:
            prefix = int(m.group(1))
            suffix = int(m.group(2))
            
            try:
                stat = os.stat(path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files.append((f, prefix, suffix, mtime, path))
            except Exception as e:
                print(f"Error reading stat for {f}: {e}")
                
    if not files:
        print("No matching files found in the root of turboflow.")
        return
        
    print(f"Found {len(files)} files matching \\d+-architectural-digest-styl-\\d+.png in the turboflow root folder.")
    
    # Sort by prefix
    files.sort(key=lambda x: x[1])
    print(f"Earliest prefix: {files[0][0]} (mtime: {files[0][3]})")
    print(f"Latest prefix: {files[-1][0]} (mtime: {files[-1][3]})")
    
    # Group by prefix ranges (e.g. 2900-3000, 3000-3100, etc.)
    ranges = {}
    for f, prefix, suffix, mtime, path in files:
        range_start = (prefix // 100) * 100
        range_end = range_start + 99
        range_name = f"{range_start}-{range_end}"
        ranges[range_name] = ranges.get(range_name, 0) + 1
        
    print("\nFile count by prefix range:")
    for range_name, count in sorted(ranges.items()):
        print(f"  {range_name}: {count} files")
        
    # List a few examples around 3340
    print("\nRecent files around 3340:")
    for f, prefix, suffix, mtime, path in files[-10:]:
        print(f"  {f} - mtime: {mtime}")

if __name__ == "__main__":
    main()
