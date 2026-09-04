import os
import re
import json
import sys

# Configure standard streams to use UTF-8 to prevent encoding issues in Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
LOCAL_REFORMA_ORIG = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-original-images"
SKU_MAP_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\sku_map.json"
ONEDRIVE_PICTURES = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
INTERIORS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-26-06"

# Load SKU map
sku_to_filename = {}
if os.path.exists(SKU_MAP_PATH):
    with open(SKU_MAP_PATH, 'r', encoding='utf-8') as f:
        sku_map = json.load(f)
        for filename, info in sku_map.items():
            sku = info.get('sku')
            if sku:
                sku_to_filename[sku] = filename

def get_sku_from_dir_name(dir_name):
    match = re.search(r'\(([^)]+)\)$', dir_name)
    if match:
        return match.group(1).strip()
    return None

def find_reference_image(dir_path, dir_name):
    # Heuristic 1: Look in the directory itself for *REFERENCE*
    for f in os.listdir(dir_path):
        if 'reference' in f.lower() and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return os.path.join(dir_path, f), "local_folder_reference"
            
    # Get SKU
    sku = get_sku_from_dir_name(dir_name)
    if not sku:
        return None, "no_sku"
        
    # Heuristic 2: Look in local reforma-original-images
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        local_path = os.path.join(LOCAL_REFORMA_ORIG, f"{sku}{ext}")
        if os.path.exists(local_path):
            return local_path, "local_reforma_original"
            
    # Heuristic 3: Check reverse mapped filename from sku_map.json
    mapped_filename = sku_to_filename.get(sku)
    
    # Heuristic 4: Look in OneDrive product folders
    product_search_dirs = [
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter"),
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter_aktiva"),
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter_aktiva_del1"),
        os.path.join(ONEDRIVE_PICTURES, "turboflow_batch2_produkter_aktiva_del2"),
    ]
    # Add batch 1 folders
    for i in range(1, 9):
        product_search_dirs.append(os.path.join(ONEDRIVE_PICTURES, f"turboflow_batch1_produkter_aktiva_del{i}"))
        
    for p_dir in product_search_dirs:
        if not os.path.exists(p_dir):
            continue
            
        # Try mapped filename first
        if mapped_filename:
            # Check direct match (allowing extension variations like .png -> .webp)
            base_mapped, _ = os.path.splitext(mapped_filename)
            for f in os.listdir(p_dir):
                base_f, _ = os.path.splitext(f)
                if base_mapped.lower() == base_f.lower():
                    return os.path.join(p_dir, f), f"onedrive_mapped_{os.path.basename(p_dir)}"
        
        # Try generic search for SKU in filenames
        for f in os.listdir(p_dir):
            if sku in f and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return os.path.join(p_dir, f), f"onedrive_sku_{os.path.basename(p_dir)}"
                
    return None, "not_found"

def main():
    print("Testing reference image resolution logic:")
    subdirs = [d for d in os.listdir(INTERIORS_DIR) if os.path.isdir(os.path.join(INTERIORS_DIR, d))]
    
    # Check first 25 folders
    found_count = 0
    for i, sd in enumerate(subdirs[:25]):
        dir_path = os.path.join(INTERIORS_DIR, sd)
        ref_path, source = find_reference_image(dir_path, sd)
        sku = get_sku_from_dir_name(sd)
        print(f"[{i+1}] Folder: {sd}")
        print(f"    SKU: {sku}")
        if ref_path:
            print(f"    FOUND: {ref_path} (Source: {source})")
            found_count += 1
        else:
            print(f"    NOT FOUND (Reason: {source})")
            
    print(f"\nResult: Found reference images for {found_count}/25 folders.")

if __name__ == "__main__":
    main()
