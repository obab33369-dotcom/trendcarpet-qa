import os
import shutil
import stat

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def merge_folders(src_dir, dest_dir):
    if not os.path.exists(src_dir):
        return 0, 0
        
    os.makedirs(dest_dir, exist_ok=True)
    make_writable(dest_dir)
    
    files_copied = 0
    dirs_created = 0
    
    for root, dirs, files in os.walk(src_dir):
        # Determine relative path from src_dir
        rel_path = os.path.relpath(root, src_dir)
        if rel_path == ".":
            target_dir = dest_dir
        else:
            target_dir = os.path.join(dest_dir, rel_path)
            
        os.makedirs(target_dir, exist_ok=True)
        make_writable(target_dir)
        
        for f in files:
            src_file = os.path.join(root, f)
            dest_file = os.path.join(target_dir, f)
            
            # If reference image, rename it to correct SKU format if needed
            # (actually, copy2 preserves filename which is fine)
            try:
                make_writable(src_file)
                if os.path.exists(dest_file):
                    make_writable(dest_file)
                    os.remove(dest_file)
                shutil.copy2(src_file, dest_file)
                files_copied += 1
            except Exception as e:
                print(f"  Failed to copy {f}: {e}")
                
    return files_copied, dirs_created

def main():
    print("=== RESTORING FURNITURE RENDERS FROM SOURCE DIRECTORIES ===")
    
    # Mappings from source folder -> target folder in Reforma-Full-Catalog-sortering
    folders_to_restore = [
        # (src_name, target_name)
        ("Bokhylla Newcastle Svart (NEWCASTLE-BLACK)", "Bokhylla Newcastle Svart (NEWCASTLE-BLACK)"),
        ("Byrå Blåvik - Natur (23101-natur)", "Byrå Blåvik - Natur (23101-natur)"),
        ("Sidobord Cardoba Natur (H000022821)", "Sidobord Cardoba Natur (H000022821)"),
        ("Sidobord Torekov - Ljus Valnöt (2251-1 Walnut)", "Sidobord Torekov - Ljus Valnöt (2251-1 Walnut)"),
        ("Sidobord Torekov - Ljus Valnöt (2251-1%20Walnut)", "Sidobord Torekov - Ljus Valnöt (2251-1 Walnut)")
    ]
    
    source_roots = [
        os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering"),
        os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-26-06")
    ]
    
    for src_folder_name, target_folder_name in folders_to_restore:
        target_dir = os.path.join(CLEAN_ROOT, target_folder_name)
        print(f"\nRestoring {target_folder_name}:")
        
        total_copied = 0
        for src_root in source_roots:
            src_dir = os.path.join(src_root, src_folder_name)
            if os.path.exists(src_dir):
                files_copied, _ = merge_folders(src_dir, target_dir)
                total_copied += files_copied
                print(f"  Merged from {os.path.basename(src_root)}: copied {files_copied} files.")
                
        # Also let's check files in target_dir
        if os.path.exists(target_dir):
            main_files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f)) and not f.startswith("00_REFERENCE_")]
            reserv_files = []
            reserv_path = os.path.join(target_dir, "reserv")
            if os.path.exists(reserv_path):
                reserv_files = [f for f in os.listdir(reserv_path) if os.path.isfile(os.path.join(reserv_path, f))]
            ref_files = [f for f in os.listdir(target_dir) if f.startswith("00_REFERENCE_")]
            print(f"  Target folder now contains: main={len(main_files)}, reserv={len(reserv_files)}, reference={ref_files}")

if __name__ == "__main__":
    main()
