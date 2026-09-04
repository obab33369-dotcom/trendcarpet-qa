import os
import stat
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# Target main directories
MAIN_CLEAN = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
MAIN_DISCARD = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

# Source carpet directories
CARPET_CLEAN = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
CARPET_DISCARD = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

def make_writable_recursive(path):
    if not os.path.exists(path):
        return
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for d in dirs:
                try:
                    os.chmod(os.path.join(root, d), stat.S_IWRITE)
                except Exception:
                    pass
            for f in files:
                try:
                    os.chmod(os.path.join(root, f), stat.S_IWRITE)
                except Exception:
                    pass

def main():
    print("=== MOVING CARPETS WITH > 3 APPROVED IMAGES BACK TO MAIN ===")
    
    if not os.path.exists(CARPET_CLEAN):
        print("Source carpet clean directory does not exist.")
        return
        
    os.makedirs(MAIN_CLEAN, exist_ok=True)
    os.makedirs(MAIN_DISCARD, exist_ok=True)
    
    folders = sorted(os.listdir(CARPET_CLEAN))
    moved_count = 0
    
    for folder in folders:
        clean_src = os.path.join(CARPET_CLEAN, folder)
        if not os.path.isdir(clean_src):
            continue
            
        # Count approved rendering files
        renders = [f for f in os.listdir(clean_src) if not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        
        if len(renders) > 3:
            print(f"\nProcessing carpet folder: {folder} ({len(renders)} approved images)")
            
            # Destination paths
            clean_dest = os.path.join(MAIN_CLEAN, folder)
            discard_src = os.path.join(CARPET_DISCARD, folder)
            discard_dest = os.path.join(MAIN_DISCARD, folder)
            
            # 1. Clear permissions on source clean folder
            make_writable_recursive(clean_src)
            
            # 2. Move clean folder
            print(f"  Moving clean folder -> {clean_dest}")
            if os.path.exists(clean_dest):
                # If target already exists, merge them
                make_writable_recursive(clean_dest)
                for f in os.listdir(clean_src):
                    src_f = os.path.join(clean_src, f)
                    dest_f = os.path.join(clean_dest, f)
                    make_writable_recursive(src_f)
                    try:
                        shutil.move(src_f, dest_f)
                    except Exception as e:
                        print(f"    Error merging clean file {f}: {e}")
                try:
                    os.rmdir(clean_src)
                except Exception as e:
                    print(f"    Error removing clean source folder {folder}: {e}")
            else:
                try:
                    shutil.move(clean_src, clean_dest)
                except Exception as e:
                    print(f"    Error moving clean folder: {e}")
            
            # 3. Move discard folder if it exists
            if os.path.exists(discard_src) and os.path.isdir(discard_src):
                make_writable_recursive(discard_src)
                print(f"  Moving discard folder -> {discard_dest}")
                if os.path.exists(discard_dest):
                    make_writable_recursive(discard_dest)
                    for f in os.listdir(discard_src):
                        src_f = os.path.join(discard_src, f)
                        dest_f = os.path.join(discard_dest, f)
                        make_writable_recursive(src_f)
                        try:
                            shutil.move(src_f, dest_f)
                        except Exception as e:
                            print(f"    Error merging discard file {f}: {e}")
                    try:
                        os.rmdir(discard_src)
                    except Exception as e:
                        print(f"    Error removing discard source folder {folder}: {e}")
                else:
                    try:
                        shutil.move(discard_src, discard_dest)
                    except Exception as e:
                        print(f"    Error moving discard folder: {e}")
            
            moved_count += 1
            
    print(f"\nSuccessfully moved {moved_count} carpet folders back to main directory.")

if __name__ == "__main__":
    main()
