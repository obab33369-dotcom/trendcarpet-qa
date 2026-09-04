import os
import re
import datetime

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    dirs = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    files_info = []
    for d in dirs:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            m = re.match(r"^(\d+)", f)
            if not m:
                continue
            prefix = int(m.group(1))
            
            # Full catalog indices are between 1 and 3340
            if 1 <= prefix <= 3340:
                path = os.path.join(d, f)
                try:
                    stat = os.stat(path)
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                    files_info.append((f, mtime, path))
                except Exception:
                    pass
                    
    if not files_info:
        print("No files found in index range 1 to 3340.")
        return
        
    print(f"Total files found in index range 1 to 3340: {len(files_info)}")
    
    # Sort by mtime
    files_info.sort(key=lambda x: x[1])
    print(f"Earliest file: {files_info[0][0]} on {files_info[0][1]}")
    print(f"Latest file: {files_info[-1][0]} on {files_info[-1][1]}")
    
    # Group by day
    days = {}
    for f, mtime, path in files_info:
        day_str = mtime.strftime("%Y-%m-%d")
        days[day_str] = days.get(day_str, 0) + 1
        
    print("\nFile count by day:")
    for day, count in sorted(days.items()):
        print(f"  {day}: {count} files")

if __name__ == "__main__":
    main()
