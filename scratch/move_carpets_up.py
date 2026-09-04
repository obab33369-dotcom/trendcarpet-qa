import os
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

def move_up_for_root(root_dir):
    if not os.path.exists(root_dir):
        print(f"Directory does not exist: {root_dir}")
        return
        
    print(f"\nProcessing root: {os.path.basename(root_dir)}")
    moved_count = 0
    folders_processed = 0
    
    for item in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, item)
        if os.path.isdir(folder_path):
            reserv_path = os.path.join(folder_path, "reserv")
            if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
                folders_processed += 1
                # Move all files from reserv to parent folder
                for f in os.listdir(reserv_path):
                    src_file = os.path.join(reserv_path, f)
                    if os.path.isfile(src_file):
                        dest_file = os.path.join(folder_path, f)
                        try:
                            # Move file, overwrite if it somehow exists
                            if os.path.exists(dest_file):
                                os.remove(dest_file)
                            shutil.move(src_file, dest_file)
                            moved_count += 1
                        except Exception as e:
                            print(f"  Failed to move {f} in {item}: {e}")
                
                # Delete empty reserv folder
                try:
                    if not os.listdir(reserv_path):
                        os.rmdir(reserv_path)
                except Exception as e:
                    print(f"  Failed to remove empty reserv dir for {item}: {e}")
                    
    print(f"Processed {folders_processed} folders. Moved {moved_count} files up to root.")

def main():
    move_up_for_root(CLEAN_ROOT)
    move_up_for_root(DISCARD_ROOT)
    print("\n=== All carpet files moved up to their root product folders ===")

if __name__ == "__main__":
    main()
