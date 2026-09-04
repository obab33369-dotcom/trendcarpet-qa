import os
import sys

TARGET_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-26-06"

def clean():
    if not os.path.exists(TARGET_DIR):
        print(f"Target directory {TARGET_DIR} does not exist.")
        return

    print(f"Scanning target directory: {TARGET_DIR}")
    deleted_count = 0
    subdirs_scanned = 0

    for entry in os.listdir(TARGET_DIR):
        subdir_path = os.path.join(TARGET_DIR, entry)
        if not os.path.isdir(subdir_path):
            continue
        
        subdirs_scanned += 1
        for filename in os.listdir(subdir_path):
            file_path = os.path.join(subdir_path, filename)
            if not os.path.isfile(file_path):
                continue
            
            # Keep studio reference photos
            if filename.startswith("00_REFERENCE_"):
                continue
                
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")

    print(f"Cleanup finished. Scanned {subdirs_scanned} subdirectories. Deleted {deleted_count} render files.")

if __name__ == '__main__':
    clean()
