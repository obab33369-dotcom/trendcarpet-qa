import os
import datetime
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
FYRKANTIGA_DIR = os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")

def main():
    if not os.path.exists(FYRKANTIGA_DIR):
        print("Folder not found.")
        return
        
    files = os.listdir(FYRKANTIGA_DIR)
    img_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    print(f"Total images in 'första omgången fyrkantiga': {len(img_files)}")
    
    # Let's check some statistics
    with_parenthesis = [f for f in img_files if "(1)" in f]
    without_parenthesis = [f for f in img_files if "(1)" not in f]
    print(f"  Files with '(1)': {len(with_parenthesis)}")
    print(f"  Files without '(1)': {len(without_parenthesis)}")
    
    # Get details with mtimes
    file_records = []
    for f in img_files:
        path = os.path.join(FYRKANTIGA_DIR, f)
        try:
            stat = os.stat(path)
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
            file_records.append((f, mtime))
        except Exception:
            pass
            
    file_records.sort(key=lambda x: x[1])
    
    print("\nEarliest files in this folder:")
    for f, mtime in file_records[:10]:
        print(f"  {f} - Modified: {mtime}")
        
    print("\nLatest files in this folder:")
    for f, mtime in file_records[-10:]:
        print(f"  {f} - Modified: {mtime}")
        
    # Group by date
    days = {}
    for f, mtime in file_records:
        d_str = mtime.strftime("%Y-%m-%d")
        days[d_str] = days.get(d_str, 0) + 1
    print("\nFile count by day in 'första omgången fyrkantiga':")
    for d, c in sorted(days.items()):
        print(f"  {d}: {c} files")

if __name__ == "__main__":
    main()
