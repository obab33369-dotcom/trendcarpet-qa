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

def redirect_carpet(src_folder_name, dest_folder_name, dest_sku):
    print(f"\n--- Redirecting {src_folder_name} -> {dest_folder_name} (SKU {dest_sku}) ---")
    
    # We will search in both CLEAN_DIR and DISCARD_DIR for the src_folder
    for root_dir in [CLEAN_DIR, DISCARD_DIR]:
        src_folder = os.path.join(root_dir, src_folder_name)
        if not os.path.exists(src_folder):
            continue
            
        # Target folder is ALWAYS in DISCARD_DIR so the user can review them under the correct reference image!
        target_folder = os.path.join(DISCARD_DIR, dest_folder_name)
        os.makedirs(target_folder, exist_ok=True)
        copy_ref_photo(dest_sku, target_folder)
        
        # 1. Move files in main directory
        for item in os.listdir(src_folder):
            src_file = os.path.join(src_folder, item)
            if os.path.isfile(src_file) and not item.startswith("00_REFERENCE_"):
                dest_file = os.path.join(target_folder, item)
                print(f"  [MOVE MAIN] {item} -> {target_folder}")
                shutil.move(src_file, dest_file)
                
        # 2. Move files in reserv directory
        src_reserv = os.path.join(src_folder, "reserv")
        if os.path.exists(src_reserv) and os.path.isdir(src_reserv):
            target_reserv = os.path.join(target_folder, "reserv")
            os.makedirs(target_reserv, exist_ok=True)
            for item in os.listdir(src_reserv):
                src_file = os.path.join(src_reserv, item)
                if os.path.isfile(src_file) and not item.startswith("00_REFERENCE_"):
                    dest_file = os.path.join(target_reserv, item)
                    print(f"  [MOVE RESERV] {item} -> {target_reserv}")
                    shutil.move(src_file, dest_file)
                    
        # Clean up empty source directory
        clean_if_empty(src_folder)

def main():
    print("=== STARTING CARPET VISUAL REDIRECTION ===")
    
    # 1. Seronis (RG01-1) -> Aravelle (RG01-19)
    redirect_carpet(
        "Matta Seronis - SvartBeige (RG01-1)",
        "Matta Aravelle - GråMulti (RG01-19)",
        "RG01-19"
    )
    
    # 2. Sorvento (RG01-49) -> Orlisse (RG01-499)
    redirect_carpet(
        "Matta Sorvento - SvartBeige (RG01-49)",
        "Matta Orlisse - Brun (RG01-499)",
        "RG01-499"
    )
    
    # 3. Velenna - SvartGrå (RG01-6) -> Arvella - Brun (RG01-64)
    redirect_carpet(
        "Matta Velenna - SvartGrå (RG01-6)",
        "Matta Arvella - Brun (RG01-64)",
        "RG01-64"
    )
    
    print("\n=== CARPET VISUAL REDIRECTION COMPLETE ===")

if __name__ == "__main__":
    main()
