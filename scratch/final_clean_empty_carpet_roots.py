import os
import shutil
import stat

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_CARPETS = os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering")
DISCARD_CARPETS = os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering-borttagna")

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def delete_empty_dirs(root_dir):
    if not os.path.exists(root_dir):
        return
    print(f"Checking folders in {root_dir}...")
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            make_writable(dir_path)
            # count files recursively
            total_files = 0
            for _, _, fs in os.walk(dir_path):
                total_files += len(fs)
            if total_files == 0:
                try:
                    shutil.rmtree(dir_path)
                    print(f"  Deleted empty folder: {os.path.relpath(dir_path, root_dir)}")
                except Exception as e:
                    print(f"  Failed to delete {d}: {e}")
            else:
                print(f"  Folder {d} is not empty (contains {total_files} files). Skipping.")
                
    # Try deleting the root folder itself if empty
    make_writable(root_dir)
    total_files = 0
    for _, _, fs in os.walk(root_dir):
        total_files += len(fs)
    if total_files == 0:
        try:
            shutil.rmtree(root_dir)
            print(f"Successfully deleted empty root: {root_dir}")
        except Exception as e:
            print(f"Failed to delete root {root_dir}: {e}")
    else:
        print(f"Root {root_dir} is not empty. Skipping.")

if __name__ == "__main__":
    delete_empty_dirs(CLEAN_CARPETS)
    delete_empty_dirs(DISCARD_CARPETS)
