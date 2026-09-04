import os
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
ORIG_DIR = os.path.join(WORKSPACE_DIR, "reforma-original-images")

def clean_if_empty(folder_path):
    if not os.path.exists(folder_path):
        return
    
    try:
        # Clean reserv if empty
        reserv = os.path.join(folder_path, "reserv")
        if os.path.exists(reserv) and os.path.isdir(reserv):
            if not os.listdir(reserv):
                os.rmdir(reserv)
                print(f"  Deleted empty reserv directory: {reserv}")
    except Exception as e:
        print(f"  Could not delete reserv directory: {e}")
            
    try:
        # Clean main folder if empty (only ref image left)
        remaining = os.listdir(folder_path)
        if len(remaining) == 1 and remaining[0].startswith("00_REFERENCE_"):
            os.remove(os.path.join(folder_path, remaining[0]))
            os.rmdir(folder_path)
            print(f"  Deleted empty product directory: {folder_path}")
        elif not remaining:
            os.rmdir(folder_path)
            print(f"  Deleted empty product directory: {folder_path}")
    except Exception as e:
        print(f"  Could not delete empty product directory {folder_path}: {e}")

def copy_ref_photo(sku, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    ref_dest = os.path.join(dest_folder, f"00_REFERENCE_{sku}.jpg")
    if os.path.exists(ref_dest):
        return
        
    ref_src_paths = [
        os.path.join(ORIG_DIR, f"{sku}.jpg"),
        os.path.join(ORIG_DIR, f"{sku}.png"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{sku}.jpg"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{sku}.png")
    ]
    
    for path in ref_src_paths:
        if os.path.exists(path):
            shutil.copy2(path, ref_dest)
            print(f"  [REF COPY] Reference photo copied to {ref_dest}")
            return

def main():
    print("=== STARTING SORVENTO -> ORLISSE REORGANIZATION ===")
    
    src_folder_name = "Matta Sorvento - SvartBeige (RG01-49)"
    dest_folder_name = "Matta Orlisse - Brun (RG01-499)"
    
    # 1. Clean Directory
    clean_src = os.path.join(CLEAN_DIR, src_folder_name)
    clean_dest = os.path.join(CLEAN_DIR, dest_folder_name)
    
    if os.path.exists(clean_src):
        print(f"Processing Clean: {src_folder_name} -> {dest_folder_name}")
        os.makedirs(clean_dest, exist_ok=True)
        copy_ref_photo("RG01-499", clean_dest)
        
        # Move reserv
        src_res = os.path.join(clean_src, "reserv")
        dest_res = os.path.join(clean_dest, "reserv")
        if os.path.exists(src_res) and os.path.isdir(src_res):
            os.makedirs(dest_res, exist_ok=True)
            for item in os.listdir(src_res):
                src_file = os.path.join(src_res, item)
                if os.path.isfile(src_file) and not item.startswith("00_REFERENCE_"):
                    shutil.move(src_file, os.path.join(dest_res, item))
                    print(f"  [MOVE CLEAN RESERV] {item} -> {dest_res}")
                    
        # Move main if any
        for item in os.listdir(clean_src):
            src_file = os.path.join(clean_src, item)
            if os.path.isfile(src_file) and not item.startswith("00_REFERENCE_"):
                shutil.move(src_file, os.path.join(clean_dest, item))
                print(f"  [MOVE CLEAN] {item} -> {clean_dest}")
                
        clean_if_empty(clean_src)
        
    # 2. Discard Directory
    discard_src = os.path.join(DISCARD_DIR, src_folder_name)
    discard_dest = os.path.join(DISCARD_DIR, dest_folder_name)
    
    if os.path.exists(discard_src):
        print(f"Processing Discard: {src_folder_name} -> {dest_folder_name}")
        os.makedirs(discard_dest, exist_ok=True)
        copy_ref_photo("RG01-499", discard_dest)
        
        # Move reserv
        src_res = os.path.join(discard_src, "reserv")
        dest_res = os.path.join(discard_dest, "reserv")
        if os.path.exists(src_res) and os.path.isdir(src_res):
            os.makedirs(dest_res, exist_ok=True)
            for item in os.listdir(src_res):
                src_file = os.path.join(src_res, item)
                if os.path.isfile(src_file) and not item.startswith("00_REFERENCE_"):
                    shutil.move(src_file, os.path.join(dest_res, item))
                    print(f"  [MOVE DISCARD RESERV] {item} -> {dest_res}")
                    
        # Move main if any
        for item in os.listdir(discard_src):
            src_file = os.path.join(discard_src, item)
            if os.path.isfile(src_file) and not item.startswith("00_REFERENCE_"):
                shutil.move(src_file, os.path.join(discard_dest, item))
                print(f"  [MOVE DISCARD] {item} -> {discard_dest}")
                
        clean_if_empty(discard_src)
        
    print("Sorvento -> Orlisse reorganization completed!")

if __name__ == "__main__":
    main()
