import os
import stat
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def remove_readonly_onerror(func, path, excinfo):
    make_writable(path)
    try:
        func(path)
    except Exception as e:
        print(f"    Failed to delete {path}: {e}")

def cleanup_root(root):
    if not os.path.exists(root):
        return 0
        
    cleaned = 0
    for d in os.listdir(root):
        dp = os.path.join(root, d)
        if os.path.isdir(dp):
            files = os.listdir(dp)
            renders = [f for f in files if not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            
            # If no renders are left, clean up the folder
            if not renders:
                print(f"Cleaning empty folder: {dp}")
                # Make all files writable first
                for f in files:
                    fp = os.path.join(dp, f)
                    make_writable(fp)
                make_writable(dp)
                
                try:
                    shutil.rmtree(dp, onerror=remove_readonly_onerror)
                    cleaned += 1
                    print(f"  Successfully removed: {d}")
                except Exception as e:
                    print(f"  Error removing {d}: {e}")
    return cleaned

def main():
    print("=== Cleaning Up Empty Carpet Directories ===")
    clean_count = cleanup_root(CLEAN_ROOT)
    discard_count = cleanup_root(DISCARD_ROOT)
    print(f"\nCleanup complete. Removed {clean_count} empty folders from clean root, and {discard_count} from discard root.")

if __name__ == "__main__":
    main()
