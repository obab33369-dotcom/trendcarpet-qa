import os
import stat

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def cleanup_roots(root_dir):
    if not os.path.exists(root_dir):
        return
        
    cleaned_count = 0
    for item in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, item)
        if os.path.isdir(folder_path):
            reserv_path = os.path.join(folder_path, "reserv")
            if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
                # Check if actually empty
                try:
                    # Clear read-only attribute on the folder
                    os.chmod(reserv_path, stat.S_IWRITE)
                    # Check files inside
                    files = os.listdir(reserv_path)
                    if not files:
                        os.rmdir(reserv_path)
                        cleaned_count += 1
                    else:
                        print(f"Folder not empty: {reserv_path} contains {files}")
                except Exception as e:
                    print(f"Could not delete {reserv_path}: {e}")
                    
    print(f"Cleaned up {cleaned_count} empty reserv folders in {os.path.basename(root_dir)}.")

def main():
    cleanup_roots(CLEAN_ROOT)
    cleanup_roots(DISCARD_ROOT)

if __name__ == "__main__":
    main()
