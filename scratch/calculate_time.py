import os
import glob
import time

artiklar_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar"

if not os.path.exists(artiklar_dir):
    print(f"Directory {artiklar_dir} does not exist.")
    exit(1)

files = glob.glob(os.path.join(artiklar_dir, "*.jpg"))
if not files:
    print("No images found in the output directory.")
    exit(0)

# Sort by modification time
files.sort(key=os.path.getmtime)
now = time.time()

# Let's count how many files were modified in the last 10 minutes (600 seconds)
ten_mins_ago = now - 600
recent_files = [f for f in files if os.path.getmtime(f) >= ten_mins_ago]
num_recent = len(recent_files)

print(f"Total files in directory: {len(files)}")
print(f"Files written in the last 10 minutes: {num_recent}")

if num_recent > 0:
    rate_per_min = num_recent / 10.0
    print(f"Processing rate: {rate_per_min:.2f} SKUs per minute.")
    
    total_remaining = 446
    est_minutes = total_remaining / rate_per_min
    hours = int(est_minutes // 60)
    minutes = int(est_minutes % 60)
    
    print(f"Estimated time to complete remaining {total_remaining} SKUs: {hours} hours and {minutes} minutes ({est_minutes:.1f} minutes).")
else:
    # Fallback to general average based on logs
    # Assume 1 SKU takes about 15 seconds average (with cache hits and parallel workers)
    avg_sec_per_sku = 12.0
    total_remaining = 446
    est_minutes = (total_remaining * avg_sec_per_sku) / 60.0
    hours = int(est_minutes // 60)
    minutes = int(est_minutes % 60)
    print("No files modified in the last 10 minutes (possibly because loop recently failed/stopped).")
    print(f"Using estimated average speed of {avg_sec_per_sku} seconds per SKU:")
    print(f"Estimated time to complete remaining {total_remaining} SKUs: {hours} hours and {minutes} minutes ({est_minutes:.1f} minutes).")
