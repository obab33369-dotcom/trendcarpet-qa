import os
import shutil
import stat
import time

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering")
DISCARD_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering-borttagna")

CLEAN_FURNITURE_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
DISCARD_FURNITURE_SRC = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering-borttagna")

# The 18 correct clean carpet folders from the latest run
CORRECT_CLEAN_CARPETS = [
    'Matta Arvella - BrunSvart (RG01-66)', 'Matta Arvella - RödGrön (RG01-65)', 
    'Matta Aureline - BeigeBrun (RG01-8)', 'Matta Aureline - Grön (RG01-9)', 
    'Matta Aureline BeigeGrå (RG01-7)', 'Matta Belden - Grön (RG01-74)', 
    'Matta Calvera - Röd (RG01-34)', 'Matta Carrano - GråVit (RG01-72)', 
    'Matta Carrano - Grön (RG01-71)', 'Matta Velenna 160x230 cm - Blå (RG016)', 
    'Matta Ventaro - BrunBeige (RG01-92)', 'Matta Ventaro - BrunGrå (RG01-86)', 
    'Matta Ventaro - Multi (RG01-87)', 'Matta Ventaro - RödOrange (RG01-88)', 
    'Matta Verona 170x230 - Beige (rug02-170x230)', 'Matta Ängelholm - GråBlå (RG002)', 
    'Matta Ängelholm - Grön (RG00)', 'Matta Ängelholm - Mörkbrun (RG001)'
]

# The 8 correct discarded carpet folders from the latest run
CORRECT_DISCARD_CARPETS = [
    'Matta Aravelle - Multi (RG01-20)', 'Matta Arvella - BrunSvart (RG01-66)', 
    'Matta Arvella - RödGrön (RG01-65)', 'Matta Belden - Grön (RG01-74)', 
    'Matta Belden - Röd (RG01-73)', 'Matta Velenna 160x230 cm - Blå (RG016)', 
    'Matta Verona 170x230 - Beige (rug02-170x230)', 'Matta Ängelholm - Mörkbrun (RG001)'
]

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
        print(f"  Warning: failed to delete {path} directly: {e}")

def robust_wipe(path):
    if not os.path.exists(path):
        return
    make_writable(path)
    parent = os.path.dirname(path)
    base = os.path.basename(path)
    temp_path = os.path.join(parent, f"{base}_todelete_{int(time.time())}")
    
    try:
        os.rename(path, temp_path)
        print(f"Successfully renamed {base} -> {os.path.basename(temp_path)} for deferred deletion.")
        wipe_read_only_tree(temp_path)
    except Exception as e:
        print(f"Could not rename {base}: {e}. Falling back to file-by-file deletion.")
        # Fallback: Delete all contents inside
        for root, dirs, files in os.walk(path, topdown=False):
            for f in files:
                f_path = os.path.join(root, f)
                make_writable(f_path)
                try:
                    os.remove(f_path)
                except Exception as ex:
                    print(f"  Could not delete file {f_path}: {ex}")
            for d in dirs:
                d_path = os.path.join(root, d)
                make_writable(d_path)
                try:
                    os.rmdir(d_path)
                except Exception as ex:
                    pass

def main():
    print("=== STARTING ROBUST CONSOLIDATED REBUILD ===")
    
    # 1. Wipe destination directories completely using robust renaming
    print("\nWiping destination directories...")
    robust_wipe(CLEAN_DST)
    robust_wipe(DISCARD_DST)
    
    os.makedirs(CLEAN_DST, exist_ok=True)
    os.makedirs(DISCARD_DST, exist_ok=True)
    
    # 2. Copy correct folders from source to destination
    print("\nCopying correct folders...")
    if os.path.exists(CLEAN_FURNITURE_SRC):
        for item in os.listdir(CLEAN_FURNITURE_SRC):
            src = os.path.join(CLEAN_FURNITURE_SRC, item)
            dst = os.path.join(CLEAN_DST, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
        print("  Finished copying approved folders.")
        
    if os.path.exists(DISCARD_FURNITURE_SRC):
        for item in os.listdir(DISCARD_FURNITURE_SRC):
            src = os.path.join(DISCARD_FURNITURE_SRC, item)
            dst = os.path.join(DISCARD_DST, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
        print("  Finished copying discarded folders.")
        
    print("\n=== REBUILD COMPLETE ===")
    
if __name__ == "__main__":
    main()
