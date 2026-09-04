import os
import datetime

zoom_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom"

print("Checking modification times for 97828 zoom files:")
for slot in range(1, 8):
    filepath = os.path.join(zoom_dir, f"97828_{slot}.jpg")
    if os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        print(f"  97828_{slot}.jpg: {dt}")
    else:
        print(f"  97828_{slot}.jpg: [NOT FOUND]")
