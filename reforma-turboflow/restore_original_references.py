import os
import shutil

SRC_UNFINISHED_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel"
DEST_UPSCALED_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"

def restore_originals():
    print("==================================================")
    print("       RESTORING UNCROPPED ORIGINAL IMAGES        ")
    print("==================================================")
    
    if not os.path.exists(SRC_UNFINISHED_DIR) or not os.path.exists(DEST_UPSCALED_DIR):
        print("Error: One of the directories does not exist!")
        return
        
    categories = sorted([d for d in os.listdir(DEST_UPSCALED_DIR) if os.path.isdir(os.path.join(DEST_UPSCALED_DIR, d))])
    print(f"Scanning {len(categories)} product folders...")
    
    restored_count = 0
    errors_count = 0
    
    for cat in categories:
        src_cat_path = os.path.join(SRC_UNFINISHED_DIR, cat)
        dest_cat_path = os.path.join(DEST_UPSCALED_DIR, cat)
        
        if not os.path.exists(src_cat_path):
            continue
            
        # Find any file starting with '00_ORIGINAL_'
        src_files = os.listdir(src_cat_path)
        orig_files = [f for f in src_files if f.startswith("00_ORIGINAL_")]
        
        for f in orig_files:
            src_file_path = os.path.join(src_cat_path, f)
            dest_file_path = os.path.join(dest_cat_path, f)
            
            try:
                # Copy the raw uncropped original file to overwrite the cropped upscaled one
                shutil.copy2(src_file_path, dest_file_path)
                restored_count += 1
            except Exception as e:
                print(f"   Error copying '{f}' for '{cat}': {e}")
                errors_count += 1
                
    print("\n==================================================")
    print("             UNCROPPED PHOTOS RESTORED!           ")
    print("==================================================")
    print(f"Successfully restored raw uncropped photos: {restored_count}")
    if errors_count > 0:
        print(f"Errors encountered: {errors_count}")
    print("==================================================")

if __name__ == "__main__":
    restore_originals()
