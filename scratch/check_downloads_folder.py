import os
import re
import datetime

DOWNLOADS_DIR = r"C:\Users\AndronikLindgren\Downloads"

def main():
    if not os.path.exists(DOWNLOADS_DIR):
        print(f"Downloads directory not found: {DOWNLOADS_DIR}")
        return
        
    print(f"Scanning Downloads directory: {DOWNLOADS_DIR}...")
    
    files_info = []
    for f in os.listdir(DOWNLOADS_DIR):
        if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
        m = re.match(r"^(\d+)", f)
        if not m:
            continue
        prefix = int(m.group(1))
        
        path = os.path.join(DOWNLOADS_DIR, f)
        try:
            stat = os.stat(path)
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
            files_info.append((f, mtime, path))
        except Exception:
            pass
            
    if not files_info:
        print("No image files found in Downloads.")
        return
        
    print(f"Total image files found in Downloads: {len(files_info)}")
    
    # Sort by mtime
    files_info.sort(key=lambda x: x[1])
    print(f"Earliest file: {files_info[0][0]} on {files_info[0][1]}")
    print(f"Latest file: {files_info[-1][0]} on {files_info[-1][1]}")
    
    # Group by day
    days = {}
    for f, mtime, path in files_info:
        day_str = mtime.strftime("%Y-%m-%d")
        days[day_str] = days.get(day_str, 0) + 1
        
    print("\nFile count by day in Downloads:")
    for day, count in sorted(days.items()):
        print(f"  {day}: {count} files")

if __name__ == "__main__":
    main()
