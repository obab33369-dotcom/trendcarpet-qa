import os
import shutil

# Src file
src_zoom = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\1200180_3.jpg"
backup_zoom = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\backup_before_correction\1200180_3.jpg"

dest_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611"

if os.path.exists(src_zoom):
    shutil.copy2(src_zoom, os.path.join(dest_dir, "dion_current.jpg"))
    print("Copied current zoom image.")
if os.path.exists(backup_zoom):
    shutil.copy2(backup_zoom, os.path.join(dest_dir, "dion_backup.jpg"))
    print("Copied backup zoom image.")
