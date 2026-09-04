import os
import re
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ORIG_DIR = os.path.join(WORKSPACE_DIR, "reforma-original-images")

# Target folders
NEW_CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
NEW_DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

# Source folders
SRC_CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
SRC_DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

# Redirection rules
REDIRECTS = {
    "RG01-1": ("RG01-19", "Matta Aravelle - GråMulti (RG01-19)"),
    "RG01-49": ("RG01-499", "Matta Orlisse - Brun (RG01-499)"),
    "RG01-6": ("RG01-64", "Matta Arvella - Brun (RG01-64)"),
    "RG01-85": ("RG01-855", "Matta Oralia - VitMulti (RG01-855)")
}

def get_sku(folder_name):
    m = re.search(r'\(([^)]+)\)', folder_name)
    if m:
        return m.group(1).strip()
    return None

def find_ref_photo_on_system(sku):
    # Search paths for references
    search_dirs = [
        ORIG_DIR,
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload_cropped_full", "artiklar"),
        os.path.join(ONEDRIVE_DIR, "temporary-ftp-upload", "artiklar"),
        os.path.join(ONEDRIVE_DIR, "from Reforma interiörer 26-06-discarded"),
    ]
    
    # Check common image extensions
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = os.path.join(d, f"{sku}{ext}")
            if os.path.exists(path):
                return path
                
    # Direct scan in any subdirectories of OneDrive starting with 'artiklar'
    for root, dirs, files in os.walk(ONEDRIVE_DIR):
        if "artiklar" in root.lower():
            for f in files:
                name, ext = os.path.splitext(f)
                if name == sku and ext.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                    return os.path.join(root, f)
                    
    return None

def copy_ref_photo(sku, target_folder):
    os.makedirs(target_folder, exist_ok=True)
    ref_dest = os.path.join(target_folder, f"00_REFERENCE_{sku}.jpg")
    
    # 1. Search system for the correct SKU reference image
    ref_path = find_ref_photo_on_system(sku)
    if ref_path:
        shutil.copy2(ref_path, ref_dest)
        print(f"  [REF COPY] Reference for SKU {sku} copied from {ref_path} to {ref_dest}")
        return True
        
    print(f"  [WARNING] Reference photo not found on system for SKU: {sku}")
    return False

def clean_empty_folders(root_dir):
    if not os.path.exists(root_dir):
        return
    for item in os.listdir(root_dir):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path) and is_carpet(item):
            # Delete reference images inside first
            for f in os.listdir(path):
                f_path = os.path.join(path, f)
                if os.path.isfile(f_path) and f.startswith("00_REFERENCE_"):
                    try:
                        os.remove(f_path)
                    except Exception:
                        pass
                elif os.path.isdir(f_path) and f == "reserv":
                    for sub_f in os.listdir(f_path):
                        sub_f_path = os.path.join(f_path, sub_f)
                        if os.path.isfile(sub_f_path) and sub_f.startswith("00_REFERENCE_"):
                            try:
                                os.remove(sub_f_path)
                            except Exception:
                                pass
                    try:
                        if not os.listdir(f_path):
                            os.rmdir(f_path)
                    except Exception:
                        pass
            try:
                if not os.listdir(path):
                    os.rmdir(path)
                    print(f"  Deleted empty old carpet directory: {item}")
            except Exception as e:
                print(f"  Failed to delete folder {item}: {e}")

def main():
    print("=== STARTING CARPET MIGRATION AND CONSOLIDATION ===")
    
    # 1. Scan source directories to find all carpet folders
    carpet_folders = set()
    for root in [SRC_CLEAN_ROOT, SRC_DISCARD_ROOT]:
        if os.path.exists(root):
            for item in os.listdir(root):
                if os.path.isdir(os.path.join(root, item)) and is_carpet(item):
                    carpet_folders.add(item)
                    
    print(f"Found {len(carpet_folders)} unique carpet directories to process.")
    
    # Group source folders by their target folder names (resolving redirects)
    target_to_sources = {}
    for folder in carpet_folders:
        sku = get_sku(folder)
        if sku in REDIRECTS:
            target_sku, target_folder = REDIRECTS[sku]
            print(f"Redirecting: {folder} -> {target_folder} (SKU: {target_sku})")
        else:
            target_sku = sku
            target_folder = folder
            
        if target_folder not in target_to_sources:
            target_to_sources[target_folder] = {
                "sku": target_sku,
                "sources": []
            }
        target_to_sources[target_folder]["sources"].append(folder)
        
    # Process each target folder
    for target_folder, info in sorted(target_to_sources.items()):
        target_sku = info["sku"]
        sources = info["sources"]
        
        print(f"\nProcessing target: {target_folder} (SKU: {target_sku})")
        
        # Collect all rendering candidate files from all sources
        candidates_main = []
        candidates_reserv = []
        
        for src_folder in sources:
            # Check both clean and discard roots
            for root_dir in [SRC_CLEAN_ROOT, SRC_DISCARD_ROOT]:
                src_path = os.path.join(root_dir, src_folder)
                if not os.path.exists(src_path):
                    continue
                
                # Check main folder
                for f in os.listdir(src_path):
                    f_path = os.path.join(src_path, f)
                    if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        candidates_main.append(f_path)
                        
                # Check reserv folder
                reserv_path = os.path.join(src_path, "reserv")
                if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
                    for f in os.listdir(reserv_path):
                        f_path = os.path.join(reserv_path, f)
                        if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            candidates_reserv.append(f_path)
                            
        total_candidates = len(candidates_main) + len(candidates_reserv)
        if total_candidates == 0:
            print(f"  No rendering files found. Skipping target folder creation.")
            continue
            
        print(f"  Found {total_candidates} rendering files (Main: {len(candidates_main)}, Reserv: {len(candidates_reserv)}).")
        
        # Create target directories under the new clean root
        dest_main_dir = os.path.join(NEW_CLEAN_ROOT, target_folder)
        os.makedirs(dest_main_dir, exist_ok=True)
        
        # Copy correct reference image
        copy_ref_photo(target_sku, dest_main_dir)
        
        # Move candidate files to destination
        # 1. Main candidates
        moved_main = 0
        for path in candidates_main:
            filename = os.path.basename(path)
            dest_path = os.path.join(dest_main_dir, filename)
            try:
                shutil.move(path, dest_path)
                moved_main += 1
            except Exception as e:
                print(f"    Failed to move {filename}: {e}")
                
        # 2. Reserv candidates
        moved_reserv = 0
        if candidates_reserv:
            dest_reserv_dir = os.path.join(dest_main_dir, "reserv")
            os.makedirs(dest_reserv_dir, exist_ok=True)
            for path in candidates_reserv:
                filename = os.path.basename(path)
                dest_path = os.path.join(dest_reserv_dir, filename)
                try:
                    shutil.move(path, dest_path)
                    moved_reserv += 1
                except Exception as e:
                    print(f"    Failed to move reserv {filename}: {e}")
                    
        print(f"  Successfully consolidated {moved_main} main files and {moved_reserv} reserv files into {dest_main_dir}")
        
    # Clean up empty folders in old roots
    print("\nCleaning up empty old carpet folders...")
    clean_empty_folders(SRC_CLEAN_ROOT)
    clean_empty_folders(SRC_DISCARD_ROOT)
    
    print("\n=== CARPET MIGRATION AND CONSOLIDATION COMPLETE ===")

if __name__ == "__main__":
    main()
