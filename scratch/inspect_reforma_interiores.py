import os
import re
import datetime

dir_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-26-06"
print("Scanning:", dir_path)

files_info = []
if os.path.exists(dir_path):
    try:
        files = os.listdir(dir_path)
        print(f"Total files: {len(files)}")
        for f in files:
            path = os.path.join(dir_path, f)
            if os.path.isfile(path) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                m = re.match(r"^(\d+)", f)
                if m:
                    num = int(m.group(1))
                    stat = os.stat(path)
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                    files_info.append((num, mtime, f))
    except Exception as e:
        print("Error:", e)
else:
    print("Does not exist.")

if files_info:
    files_info.sort(key=lambda x: x[0])
    min_num = files_info[0][0]
    max_num = files_info[-1][0]
    
    # Sort by time
    files_info.sort(key=lambda x: x[1])
    min_time = files_info[0][1]
    max_time = files_info[-1][1]
    
    print(f"Number Range: {min_num} to {max_num}")
    print(f"Time Range (mtime): {min_time} to {max_time}")
    
    by_date = {}
    for num, mtime, f in files_info:
        date_str = mtime.strftime("%Y-%m-%d")
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(num)
        
    print("\nBatches by date:")
    for date_str, nums in sorted(by_date.items()):
        print(f"  Date: {date_str} | Count: {len(nums)} | Min Num: {min(nums)} | Max Num: {max(nums)}")
else:
    print("No matching files found.")
