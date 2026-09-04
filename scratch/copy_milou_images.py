import os
import shutil

src_zoom = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\1400034_3.jpg"
backup_zoom = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\backup_before_correction\1400034_3.jpg"
source_image = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\3534_pall-milou-rektangulär-grå-3-26U-wonder.webp"

dest_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611"

if os.path.exists(src_zoom):
    shutil.copy2(src_zoom, os.path.join(dest_dir, "milou_current.jpg"))
    print("Copied current zoom image.")
if os.path.exists(backup_zoom):
    shutil.copy2(backup_zoom, os.path.join(dest_dir, "milou_backup.jpg"))
    print("Copied backup zoom image.")
if os.path.exists(source_image):
    shutil.copy2(source_image, os.path.join(dest_dir, "milou_source.webp"))
    print("Copied source image.")
