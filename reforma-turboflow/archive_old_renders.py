import os
import shutil
import datetime

PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
ARCHIVE_DIR = os.path.join(PICS_DIR, "arkiv_gamla_sorterade")

def archive():
    if not os.path.exists(PICS_DIR):
        print(f"Directory {PICS_DIR} does not exist.")
        return

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    print(f"Archiving old renders (before June 8th) from: {PICS_DIR}")
    print(f"Target archive directory: {ARCHIVE_DIR}")

    files = [f for f in os.listdir(PICS_DIR) if os.path.isfile(os.path.join(PICS_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    cutoff_date = datetime.datetime(2026, 6, 8)
    moved_count = 0

    for f in files:
        filepath = os.path.join(PICS_DIR, f)
        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        
        if dt < cutoff_date:
            dest_path = os.path.join(ARCHIVE_DIR, f)
            try:
                shutil.move(filepath, dest_path)
                moved_count += 1
            except Exception as e:
                print(f"❌ Error moving {f}: {e}")

    print(f"Archiving finished. Moved {moved_count} old renders to {ARCHIVE_DIR}.")

if __name__ == '__main__':
    archive()
