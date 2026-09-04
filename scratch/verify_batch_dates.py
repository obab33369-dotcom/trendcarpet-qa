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
            suffix = int(m.group(2))
            try:
                stat = os.stat(path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files.append((prefix, suffix, mtime, f))
            except Exception:
                pass
                
    if not files:
        print("No files found.")
        return
        
    # Sort files by prefix
    files.sort(key=lambda x: x[0])
    
    # We will identify batches by looking at where the suffix resets or goes back to 1
    batches = []
    current_batch = []
    
    # Alternatively, let's define the known boundaries based on suffix transitions:
    # We saw:
    # 1593 to 2151 (suffix 1 to 559)
    # 2152 to 2455 (suffix 1 to 304)
    # 2456 to 2716 (suffix 1 to 261)
    # 2717 to 3020 (suffix 1 to 304)
    # 3021 to 3340 (suffix 1 to 320)
    
    defined_ranges = [
        (1593, 2151, "Batch A"),
        (2152, 2455, "Batch B"),
        (2456, 2716, "Batch C"),
        (2717, 3020, "Batch D"),
        (3021, 3340, "Batch E")
    ]
    
    print("Mapping of the batches on disk:")
    for start, end, label in defined_ranges:
        batch_files = [x for x in files if start <= x[0] <= end]
        if not batch_files:
            print(f"  {label} ({start} to {end}): No files found on disk.")
            continue
            
        mtimes = [x[2] for x in batch_files]
        min_mtime = min(mtimes)
        max_mtime = max(mtimes)
        count = len(batch_files)
        expected_count = end - start + 1
        
        print(f"  {label}: Numbers {start} to {end}")
        print(f"    Expected count: {expected_count}, Found on disk: {count}")
        print(f"    Date range (mtime): {min_mtime.strftime('%Y-%m-%d %H:%M')} to {max_mtime.strftime('%Y-%m-%d %H:%M')}")
        
if __name__ == "__main__":
    main()
