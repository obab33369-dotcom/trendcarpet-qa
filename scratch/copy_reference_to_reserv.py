import os
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def copy_ref_to_reserv(root_dir):
    if not os.path.exists(root_dir):
        print(f"Directory not found: {root_dir}")
        return 0
        
    print(f"\nScanning: {root_dir}")
    copied_count = 0
    folders = [f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))]
    
    for f in folders:
        path = os.path.join(root_dir, f)
        
        # Check if reserv folder exists
        reserv_path = os.path.join(path, "reserv")
        if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
            # Locate reference image in root folder
            ref_file = None
            for item in os.listdir(path):
                if item.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(path, item)):
                    ref_file = item
                    break
                    
            if ref_file:
                src_ref = os.path.join(path, ref_file)
                dest_ref = os.path.join(reserv_path, ref_file)
                try:
                    shutil.copy2(src_ref, dest_ref)
                    copied_count += 1
                except Exception as e:
                    print(f"  Error copying to {f}/reserv: {e}")
                    
    print(f"Copied {copied_count} reference files to '/reserv' folders.")
    return copied_count

def main():
    dirs = [
        os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering"),
        os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering")
    ]
    
    total_copied = 0
    for d in dirs:
        total_copied += copy_ref_to_reserv(d)
        
    print(f"\nDone! Copied a total of {total_copied} reference files.")

if __name__ == "__main__":
    main()
