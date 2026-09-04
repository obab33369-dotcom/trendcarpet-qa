import os
import re
import datetime

turboflow_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

files_info = []
if os.path.exists(turboflow_dir):
    for f in os.listdir(turboflow_dir):
        path = os.path.join(turboflow_dir, f)
        if os.path.isfile(path) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            m = re.match(r"^(\d+)", f)
            if m:
                num = int(m.group(1))
                stat = os.stat(path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files_info.append((num, mtime, f))

if files_info:
    # Sort by number
    files_info.sort(key=lambda x: x[0])
    min_num = files_info[0][0]
    max_num = files_info[-1][0]
    
    # Sort by time to find the latest files
    files_info.sort(key=lambda x: x[1])
    min_time = files_info[0][1]
    max_time = files_info[-1][1]
    
    print(f"Number Range: {min_num} to {max_num}")
    print(f"Time Range (mtime): {min_time} to {max_time}")
    
    # Group by date to see what batches exist
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
