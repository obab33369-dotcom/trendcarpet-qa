import os

onedrive_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ftp_dir = os.path.join(onedrive_dir, "26-06-18-FTP")

subfolders = [
    os.path.join(ftp_dir, "artiklar", "liten"),
    os.path.join(ftp_dir, "artiklar", "zoom"),
    os.path.join(ftp_dir, "Inte-dessa-Uppdaterade-på-sajt-undersök-FTP", "artiklar", "liten"),
    os.path.join(ftp_dir, "Inte-dessa-Uppdaterade-på-sajt-undersök-FTP", "artiklar", "zoom")
]

print("==================================================")
print("CLEARING NESTED LITEN/ZOOM SUBFOLDERS IN FTP")
print("==================================================")

for folder in subfolders:
    if os.path.exists(folder):
        deleted = 0
        for f in os.listdir(folder):
            file_p = os.path.join(folder, f)
            if os.path.isfile(file_p):
                try:
                    os.remove(file_p)
                    deleted += 1
                except Exception as e:
                    print(f"  Error deleting {f} in {folder}: {e}")
        print(f"Cleaned {deleted} files from {folder}")
    else:
        print(f"Folder {folder} does not exist. Skipping.")
