import os
import stat
import shutil

PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
TURBOFLOW_ROOT = os.path.join(PICTURES_DIR, "turboflow")

CLEAN_FURNITURE_ROOT = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
CLEAN_CARPET_ROOT = os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering")

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def wipe_read_only_tree(path):
    if not os.path.exists(path):
        return
    print(f"Wiping directory: {path}...")
    for root, dirs, files in os.walk(path):
        for d in dirs:
            make_writable(os.path.join(root, d))
        for f in files:
            make_writable(os.path.join(root, f))
    try:
        shutil.rmtree(path)
        print(f"Successfully wiped: {path}")
    except Exception as e:
        print(f"Error cleaning {path}: {e}")

def main():
    wipe_read_only_tree(CLEAN_FURNITURE_ROOT)
    wipe_read_only_tree(CLEAN_CARPET_ROOT)

if __name__ == "__main__":
    main()
