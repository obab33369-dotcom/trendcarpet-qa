import os
import re
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
OLD_DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering-borttagna")
NEW_CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
NEW_DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def extract_sku(folder_name):
    # Extracts the SKU inside parentheses at the end of the folder name
    m = re.search(r"\(([^)]+)\)$", folder_name)
    if m:
        return m.group(1).strip()
    return None

def extract_unique_code(filename):
    base, _ = os.path.splitext(filename)
    base = re.sub(r'\s*\(\d+\)\s*$', '', base)
    base = re.sub(r'[-_]\s*copy\s*$', '', base, flags=re.IGNORECASE)
    
    m_new = re.search(r'-(\d+)-(\d+)$', base)
    if m_new:
        return f"{m_new.group(1)}-{m_new.group(2)}"
        
    first_m = re.match(r'^(\d+)', base)
    last_m = re.search(r'(\d+)$', base)
    if first_m and last_m:
        return f"{first_m.group(1)}-{last_m.group(1)}"
        
    return None

def make_writable(path):
    try:
        import stat
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def wipe_contents(path):
    if not os.path.exists(path):
        return
    print(f"Wiping contents of: {path}...")
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        make_writable(item_path)
        if os.path.isdir(item_path):
            for root, dirs, files in os.walk(item_path):
                for d in dirs:
                    make_writable(os.path.join(root, d))
                for f in files:
                    make_writable(os.path.join(root, f))
            try:
                shutil.rmtree(item_path)
            except Exception as e:
                print(f"Error deleting folder {item_path}: {e}")
        else:
            try:
                os.remove(item_path)
            except Exception as e:
                print(f"Error removing file {item_path}: {e}")

def main():
    print("=== STARTING EXCLUSIVE DISCARD SYNC (NO GEMINI CALLS) ===")
    
    if not os.path.exists(OLD_DISCARD_DIR):
        print(f"Error: Previous discarded directory not found at {OLD_DISCARD_DIR}")
        return
        
    if not os.path.exists(NEW_CLEAN_DIR):
        print(f"Error: New clean directory not found at {NEW_CLEAN_DIR}")
        return

    # Wipe the new discard directory before starting the sync
    wipe_contents(NEW_DISCARD_DIR)

    # 1. Build database of previously discarded images grouped by SKU and subfolder (main or reserv)
    # Map: SKU -> { "main": set(unique_codes), "reserv": set(unique_codes) }
    discarded_db = {}
    
    old_folders = [f for f in os.listdir(OLD_DISCARD_DIR) if os.path.isdir(os.path.join(OLD_DISCARD_DIR, f))]
    for folder in old_folders:
        sku = extract_sku(folder)
        if not sku:
            continue
            
        if sku not in discarded_db:
            discarded_db[sku] = {"main": set(), "reserv": set()}
            
        folder_path = os.path.join(OLD_DISCARD_DIR, folder)
        
        # Scan main files
        for item in os.listdir(folder_path):
            path = os.path.join(folder_path, item)
            if os.path.isfile(path) and not item.startswith("00_REFERENCE_"):
                code = extract_unique_code(item)
                if code:
                    discarded_db[sku]["main"].add(code)
                
        # Scan reserv files
        reserv_path = os.path.join(folder_path, "reserv")
        if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
            for item in os.listdir(reserv_path):
                path = os.path.join(reserv_path, item)
                if os.path.isfile(path) and not item.startswith("00_REFERENCE_"):
                    code = extract_unique_code(item)
                    if code:
                        discarded_db[sku]["reserv"].add(code)
                    
    total_db_entries = sum(len(v["main"]) + len(v["reserv"]) for v in discarded_db.values())
    print(f"Loaded {total_db_entries} discarded decisions from the previous cleanup.")

    # 2. Scan new clean folder and sync discards
    new_folders = [f for f in os.listdir(NEW_CLEAN_DIR) if os.path.isdir(os.path.join(NEW_CLEAN_DIR, f))]
    
    moved_count = 0
    affected_folders = set()
    
    for folder in new_folders:
        sku = extract_sku(folder)
        if not sku or sku not in discarded_db:
            continue
            
        folder_path = os.path.join(NEW_CLEAN_DIR, folder)
        dest_folder_path = os.path.join(NEW_DISCARD_DIR, folder)
        
        # Find reference image in clean folder to copy later if needed
        ref_file = None
        for item in os.listdir(folder_path):
            if item.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(folder_path, item)):
                ref_file = item
                break
        
        # Check main files
        for item in os.listdir(folder_path):
            path = os.path.join(folder_path, item)
            if os.path.isfile(path) and not item.startswith("00_REFERENCE_"):
                code = extract_unique_code(item)
                if code and code in discarded_db[sku]["main"]:
                    # Move to discard folder
                    os.makedirs(dest_folder_path, exist_ok=True)
                    src_file = path
                    dest_file = os.path.join(dest_folder_path, item)
                    
                    print(f"Moving main: {folder}/{item} -> borttagna")
                    shutil.move(src_file, dest_file)
                    moved_count += 1
                    affected_folders.add(folder)
                    
        # Check reserv files
        reserv_path = os.path.join(folder_path, "reserv")
        if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
            for item in os.listdir(reserv_path):
                path = os.path.join(reserv_path, item)
                if os.path.isfile(path) and not item.startswith("00_REFERENCE_"):
                    code = extract_unique_code(item)
                    if code and code in discarded_db[sku]["reserv"]:
                        # Move to discard reserv folder
                        dest_reserv_path = os.path.join(dest_folder_path, "reserv")
                        os.makedirs(dest_reserv_path, exist_ok=True)
                        src_file = path
                        dest_file = os.path.join(dest_reserv_path, item)
                        
                        print(f"Moving reserv: {folder}/reserv/{item} -> borttagna/reserv")
                        shutil.move(src_file, dest_file)
                        moved_count += 1
                        affected_folders.add(folder)

        # If any files were moved, make sure the reference image is copied to the discard folder
        if folder in affected_folders and ref_file:
            # Copy reference to rot of discard folder
            ref_src = os.path.join(folder_path, ref_file)
            ref_dest = os.path.join(dest_folder_path, ref_file)
            if not os.path.exists(ref_dest):
                shutil.copy2(ref_src, ref_dest)
                
            # If discard reserv exists, copy reference there too
            dest_reserv_path = os.path.join(dest_folder_path, "reserv")
            if os.path.exists(dest_reserv_path):
                ref_reserv_dest = os.path.join(dest_reserv_path, ref_file)
                if not os.path.exists(ref_reserv_dest):
                    shutil.copy2(ref_src, ref_reserv_dest)

    print(f"\nSync finished! Moved {moved_count} discarded renders across {len(affected_folders)} folders.")

if __name__ == "__main__":
    main()
