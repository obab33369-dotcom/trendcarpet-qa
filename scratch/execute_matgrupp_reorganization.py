import os
import re
import shutil
import json

ONEDRIVE_DIR = r"C:\Users\Androniklogin\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
# Use correct login username
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
ORIG_DIR = os.path.join(WORKSPACE_DIR, "reforma-original-images")

# Load DB
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")
with open(db_path, 'r', encoding='utf-8') as f:
    full_catalog_db = json.load(f)

# Convert list to dict for fast lookup
db_dict = {}
for item in full_catalog_db:
    prompt = item.get('prompt', '')
    m = re.match(r"^(\d+)", prompt)
    if m:
        prefix = int(m.group(1))
        db_dict[prefix] = item

def has_barstools(filename):
    m = re.match(r"^(\d+)", filename)
    if m:
        prefix = int(m.group(1))
        if prefix in db_dict:
            prompt = db_dict[prefix].get('prompt', '').lower()
            refs = db_dict[prefix].get('image_references', '').lower()
            keywords = ['barstol', 'bar-stol', 'barstool', 'bar table', 'barbord', 'counter stool', 'bar chair']
            if any(k in prompt or k in refs for k in keywords):
                return True
    return False

def move_files_with_check(src_folder, dest_folder, is_reserv=False):
    if not os.path.exists(src_folder):
        return 0, 0
        
    os.makedirs(dest_folder, exist_ok=True)
    moved_count = 0
    skipped_count = 0
    
    for item in os.listdir(src_folder):
        src_file = os.path.join(src_folder, item)
        if not os.path.isfile(src_file) or item.startswith("00_REFERENCE_"):
            continue
            
        # Check barstools
        if has_barstools(item):
            print(f"  [SKIP] {item} contains barstools. Keeping in source.")
            skipped_count += 1
            continue
            
        dest_file = os.path.join(dest_folder, item)
        print(f"  [MOVE] {item} -> {dest_folder}")
        shutil.move(src_file, dest_file)
        moved_count += 1
        
    return moved_count, skipped_count

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
            
    # Fallback scan
    if os.path.exists(ORIG_DIR):
        for f in os.listdir(ORIG_DIR):
            if sku.lower() in f.lower() and f.lower().endswith(('.jpg', '.png')):
                shutil.copy2(os.path.join(ORIG_DIR, f), ref_dest)
                print(f"  [REF COPY] Reference photo (fallback) copied to {ref_dest}")
                return

def main():
    print("=== STARTING MATGRUPP & MATTA REORGANIZATION ===")
    
    # Map from matgrupp folder substring to target dining table info
    # (target_folder_name, sku)
    matgrupp_mappings = {
        "Hornstull Forma": ("Matbord Hornstull 160x90cm - EkSvart (19787)", "19787"),
        "Kungsholmen Hornstull": ("Matbord Hornstull 160x90cm - EkSvart (19787)", "19787"),
        "Kungsholmen Montmartre": ("Matbord Kungsholmen (kungsholmen-bord)", "kungsholmen-bord"),
        "Runt Kungsholmen": ("Matbord Kungsholmen Runt (kungsholmen-runt-bord)", "kungsholmen-runt-bord"),
        "Vega Elsa": ("Matbord Vega 180x90cm - NaturSvart (1330)", "1330"),
        "Nordisk Elsa": ("Matbord Nordisk 120x70cm - Ek (DA-1019)", "DA-1019"),
        "Marbelous Elsa": ("Matbord Marbleous Runt 100cm - MässingVit (st-051w-100)", "st-051w-100")
    }
    
    # ----------------------------------------------------
    # 1. PROCESS MATGRUPP FOLDERS IN DISCARD DIRECTORY
    # ----------------------------------------------------
    print("\n--- Processing Matgrupp folders in Discard Directory ---")
    if os.path.exists(DISCARD_DIR):
        for folder in os.listdir(DISCARD_DIR):
            folder_path = os.path.join(DISCARD_DIR, folder)
            if not os.path.isdir(folder_path) or 'matgrupp' not in folder.lower():
                continue
                
            # Find matching mapping
            target_info = None
            for key, info in matgrupp_mappings.items():
                if key.lower() in folder.lower():
                    target_info = info
                    break
                    
            if not target_info:
                print(f"No mapping found for folder: {folder}")
                continue
                
            dest_folder_name, dest_sku = target_info
            dest_folder = os.path.join(DISCARD_DIR, dest_folder_name)
            
            print(f"Processing {folder} -> {dest_folder_name} (SKU {dest_sku})")
            
            # Copy reference photo first
            if not dest_sku.startswith("kungsholmen"):
                copy_ref_photo(dest_sku, dest_folder)
            else:
                # If no specific table SKU, copy the matgrupp reference photo
                os.makedirs(dest_folder, exist_ok=True)
                ref_file = None
                for item in os.listdir(folder_path):
                    if item.startswith("00_REFERENCE_"):
                        ref_file = item
                        break
                if ref_file:
                    dest_ref = os.path.join(dest_folder, f"00_REFERENCE_{dest_sku}.jpg")
                    if not os.path.exists(dest_ref):
                        shutil.copy2(os.path.join(folder_path, ref_file), dest_ref)
                        print(f"  [REF COPY] Matgrupp ref photo copied as {dest_ref}")
            
            # Move main files
            moved, skipped = move_files_with_check(folder_path, dest_folder, is_reserv=False)
            
            # Move reserv files
            src_reserv = os.path.join(folder_path, "reserv")
            dest_reserv = os.path.join(dest_folder, "reserv")
            moved_res, skipped_res = move_files_with_check(src_reserv, dest_reserv, is_reserv=True)
            
            print(f"  Main: moved {moved}, skipped {skipped}. Reserv: moved {moved_res}, skipped {skipped_res}.")
            
            # Clean up empty source directory
            clean_if_empty(folder_path)
            
    # ----------------------------------------------------
    # 2. PROCESS MATTA SERONIS -> MATTA ARAVELLE (DISCARD & CLEAN)
    # ----------------------------------------------------
    print("\n--- Processing Matta Seronis -> Matta Aravelle - Grå/Multi ---")
    
    seronis_folder_name = "Matta Seronis - SvartBeige (RG01-1)"
    arabelle_folder_name = "Matta Aravelle - GråMulti (RG01-19)"
    
    # A. In Clean Directory
    clean_seronis = os.path.join(CLEAN_DIR, seronis_folder_name)
    clean_arabelle = os.path.join(CLEAN_DIR, arabelle_folder_name)
    
    if os.path.exists(clean_seronis):
        print(f"Processing Clean: {seronis_folder_name} -> {arabelle_folder_name}")
        os.makedirs(clean_arabelle, exist_ok=True)
        copy_ref_photo("RG01-19", clean_arabelle)
        
        # Move main
        for item in os.listdir(clean_seronis):
            src = os.path.join(clean_seronis, item)
            if os.path.isfile(src) and not item.startswith("00_REFERENCE_"):
                shutil.move(src, os.path.join(clean_arabelle, item))
                print(f"  [MOVE CLEAN] {item} -> {clean_arabelle}")
                
        # Move reserv
        src_res = os.path.join(clean_seronis, "reserv")
        dest_res = os.path.join(clean_arabelle, "reserv")
        if os.path.exists(src_res) and os.path.isdir(src_res):
            os.makedirs(dest_res, exist_ok=True)
            for item in os.listdir(src_res):
                src = os.path.join(src_res, item)
                if os.path.isfile(src) and not item.startswith("00_REFERENCE_"):
                    shutil.move(src, os.path.join(dest_res, item))
                    print(f"  [MOVE CLEAN RESERV] {item} -> {dest_res}")
                    
        clean_if_empty(clean_seronis)
        
    # B. In Discard Directory
    discard_seronis = os.path.join(DISCARD_DIR, seronis_folder_name)
    discard_arabelle = os.path.join(DISCARD_DIR, arabelle_folder_name)
    
    if os.path.exists(discard_seronis):
        print(f"Processing Discard: {seronis_folder_name} -> {arabelle_folder_name}")
        os.makedirs(discard_arabelle, exist_ok=True)
        copy_ref_photo("RG01-19", discard_arabelle)
        
        # Move main
        for item in os.listdir(discard_seronis):
            src = os.path.join(discard_seronis, item)
            if os.path.isfile(src) and not item.startswith("00_REFERENCE_"):
                shutil.move(src, os.path.join(discard_arabelle, item))
                print(f"  [MOVE DISCARD] {item} -> {discard_arabelle}")
                
        # Move reserv
        src_res = os.path.join(discard_seronis, "reserv")
        dest_res = os.path.join(discard_arabelle, "reserv")
        if os.path.exists(src_res) and os.path.isdir(src_res):
            os.makedirs(dest_res, exist_ok=True)
            for item in os.listdir(src_res):
                src = os.path.join(src_res, item)
                if os.path.isfile(src) and not item.startswith("00_REFERENCE_"):
                    shutil.move(src, os.path.join(dest_res, item))
                    print(f"  [MOVE DISCARD RESERV] {item} -> {dest_res}")
                    
        clean_if_empty(discard_seronis)
        
    print("\nMatgrupp and Matta reorganization completed!")

if __name__ == "__main__":
    main()
