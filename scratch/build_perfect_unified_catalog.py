import os
import shutil
import stat
import time

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering")
DISCARD_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering-borttagna")

FURNITURE_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
FURNITURE_DISCARD_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering-borttagna")

CARPET_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering-NEW")

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
        print(f"  Warning: failed to delete {path}: {e}")

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
        print(f"Could not rename {base}: {e}. Falling back to file-by-file deletion.")
        # Fallback to file-by-file deletion
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
        try:
            os.rmdir(path)
        except Exception:
            pass

def main():
    print("=== BUILDING PERFECT UNIFIED CATALOG ===")
    
    # 1. Wipe old destination folders using robust renaming
    print("\nWiping old destination directories...")
    robust_wipe(CLEAN_DST)
    robust_wipe(DISCARD_DST)
    
    os.makedirs(CLEAN_DST, exist_ok=True)
    os.makedirs(DISCARD_DST, exist_ok=True)
    
    # 2. Copy corrected furniture folders
    print("\nCopying corrected furniture folders...")
    if os.path.exists(FURNITURE_SRC):
        for item in os.listdir(FURNITURE_SRC):
            src = os.path.join(FURNITURE_SRC, item)
            dst = os.path.join(CLEAN_DST, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
        print("  Finished copying approved furniture.")
        
    if os.path.exists(FURNITURE_DISCARD_SRC):
        for item in os.listdir(FURNITURE_DISCARD_SRC):
            src = os.path.join(FURNITURE_DISCARD_SRC, item)
            dst = os.path.join(DISCARD_DST, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
        print("  Finished copying discarded furniture.")
        
    # 3. Copy clean carpet folders
    print("\nCopying clean carpet folders...")
    if os.path.exists(CARPET_SRC):
        for item in os.listdir(CARPET_SRC):
            src = os.path.join(CARPET_SRC, item)
            dst = os.path.join(CLEAN_DST, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
        print("  Finished copying carpets.")
        
    # 4. Verify new totals
    print("\n" + "="*80)
    print("VERIFYING NEW TOTALS:")
    if os.path.exists(CLEAN_DST):
        subdirs = [d for d in os.listdir(CLEAN_DST) if os.path.isdir(os.path.join(CLEAN_DST, d))]
        total_files = 0
        for r, ds, fs in os.walk(CLEAN_DST):
            total_files += len(fs)
        print(f"  Approved folder: {CLEAN_DST}")
        print(f"    Subdirs: {len(subdirs)}, Total files recursively: {total_files}")
        
    if os.path.exists(DISCARD_DST):
        subdirs = [d for d in os.listdir(DISCARD_DST) if os.path.isdir(os.path.join(DISCARD_DST, d))]
        total_files = 0
        for r, ds, fs in os.walk(DISCARD_DST):
            total_files += len(fs)
        print(f"  Discarded folder: {DISCARD_DST}")
        print(f"    Subdirs: {len(subdirs)}, Total files recursively: {total_files}")
    print("="*80)

if __name__ == "__main__":
    main()
