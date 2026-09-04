import os
import re
import datetime

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    if not os.path.exists(TURBOFLOW_ROOT):
        print(f"Directory not found: {TURBOFLOW_ROOT}")
        return
        
    files = []
    for f in os.listdir(TURBOFLOW_ROOT):
        path = os.path.join(TURBOFLOW_ROOT, f)
        if not os.path.isfile(path):
            continue
        m = re.match(r"^(\d+)-architectural-digest-styl-(\d+)\.png$", f)
        if m:
            prefix = int(m.group(1))
            try:
                stat = os.stat(path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files.append((prefix, mtime.date(), f))
            except Exception:
                pass
                
    if not files:
        print("No matching files found.")
        return
        
    # Group by date
    by_date = {}
    for prefix, dt, fname in files:
        if dt not in by_date:
            by_date[dt] = []
        by_date[dt].append(prefix)
        
    print("Batch numbers by modification date:")
    for dt in sorted(by_date.keys()):
        prefixes = sorted(by_date[dt])
        count = len(prefixes)
        min_prefix = prefixes[0]
        max_prefix = prefixes[-1]
        print(f"  Date: {dt} -> Count: {count} files, Numbers: {min_prefix} to {max_prefix}")

if __name__ == "__main__":
    main()
