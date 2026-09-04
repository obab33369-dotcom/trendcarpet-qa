import os
import shutil
import stat
import time

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
DISCARD_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering-borttagna")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return ("matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower) and "_todelete_" not in name_lower

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def wipe_read_only_tree(path):
    if not os.path.exists(path):
        return
    for root, dirs, files in os.walk(path):
        for d in dirs:
            make_writable(os.path.join(root, d))
        for f in files:
            make_writable(os.path.join(root, f))
    try:
        shutil.rmtree(path)
    except Exception as e:
        pass

def robust_wipe(path):
    if not os.path.exists(path):
        return
    make_writable(path)
    parent = os.path.dirname(path)
    base = os.path.basename(path)
    temp_path = os.path.join(parent, f"{base}_todelete_{int(time.time())}")
    
    try:
        os.rename(path, temp_path)
        wipe_read_only_tree(temp_path)
    except Exception as e:
        # Fallback to file-by-file deletion if rename fails
        for root, dirs, files in os.walk(path, topdown=False):
            for f in files:
                f_path = os.path.join(root, f)
                make_writable(f_path)
                try:
                    os.remove(f_path)
                except Exception:
                    pass
            for d in dirs:
                d_path = os.path.join(root, d)
                make_writable(d_path)
                try:
                    os.rmdir(d_path)
                except Exception:
                    pass
        # Try once more to delete the folder itself
        try:
            os.rmdir(path)
        except Exception:
            pass

def clean_source(root_dir):
    if not os.path.exists(root_dir):
        return
    print(f"\nCleaning carpet folders from {os.path.basename(root_dir)}:")
    carpet_dirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d)) and is_carpet(d)]
    print(f"Found {len(carpet_dirs)} carpet folders to remove.")
    
    for d in carpet_dirs:
        path = os.path.join(root_dir, d)
        robust_wipe(path)
        print(f"  Processed removal of: {d}")

if __name__ == "__main__":
    clean_source(CLEAN_SRC)
    clean_source(DISCARD_SRC)
    print("\nSource cleaning complete.")
