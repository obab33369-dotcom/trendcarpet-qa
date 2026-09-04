import os
import re
import json
import collections

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

# Load resolver and database
import sys
sys.path.append(os.path.join(WORKSPACE_DIR, "scratch"))
from test_fixed_resolver_v2 import final_resolve_anchor

db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")
with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

# Index database by prefix
full_catalog = {}
for item in db:
    prompt = item.get('prompt', '')
    m = re.match(r'^(\d+)\s*-', prompt)
    if m:
        idx = int(m.group(1))
        full_catalog[idx] = {
            "refs": [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
        }

def main():
    print("=== SCANNING FOR ANY REMAINING MISCLASSIFICATIONS ===")
    
    total_files_scanned = 0
    misclassified_by_folder = collections.defaultdict(list)
    no_index_files = []
    unknown_index_files = []
    
    for root_dir in [CLEAN_DIR, DISCARD_DIR]:
        if not os.path.exists(root_dir):
            continue
            
        print(f"Scanning root: {root_dir}")
        for folder in os.listdir(root_dir):
            folder_path = os.path.join(root_dir, folder)
            if not os.path.isdir(folder_path):
                continue
                
            # Parse SKU from folder
            m_sku = re.search(r'\(([^)]+)\)$', folder)
            folder_sku = m_sku.group(1) if m_sku else None
            if not folder_sku:
                continue
                
            # Scan files in main folder and reserv
            folders_to_scan = [folder_path]
            reserv_path = os.path.join(folder_path, "reserv")
            if os.path.exists(reserv_path):
                folders_to_scan.append(reserv_path)
                
            for current_dir in folders_to_scan:
                is_reserv = (current_dir == reserv_path)
                for f in os.listdir(current_dir):
                    f_path = os.path.join(current_dir, f)
                    if not os.path.isfile(f_path):
                        continue
                    if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        continue
                    if f.startswith("00_REFERENCE_"):
                        continue
                        
                    total_files_scanned += 1
                    
                    # Parse index from filename
                    m_idx = re.match(r'^(\d+)-', f)
                    if not m_idx:
                        no_index_files.append((folder, f))
                        continue
                        
                    idx = int(m_idx.group(1))
                    if idx not in full_catalog:
                        unknown_index_files.append((folder, f, idx))
                        continue
                        
                    # Resolve correct SKUs
                    correct_skus = []
                    refs = full_catalog[idx]["refs"]
                    for ref in refs:
                        sku, name = final_resolve_anchor(ref)
                        if sku:
                            correct_skus.append(sku)
                            
                    if not correct_skus:
                        # Couldn't resolve any SKU for this index
                        unknown_index_files.append((folder, f, idx))
                        continue
                        
                    if folder_sku not in correct_skus:
                        misclassified_by_folder[folder].append({
                            "file": f,
                            "is_reserv": is_reserv,
                            "index": idx,
                            "expected_skus": correct_skus
                        })

    print(f"\nScan complete. Total rendering files scanned: {total_files_scanned}")
    print(f"Files with no numeric index prefix: {len(no_index_files)}")
    print(f"Files with unknown/unresolved index in DB: {len(unknown_index_files)}")
    print(f"Folders containing misclassified files: {len(misclassified_by_folder)}")
    
    if misclassified_by_folder:
        print("\n=== DETAIL OF REMAINING MISCLASSIFICATIONS ===")
        for folder, files in misclassified_by_folder.items():
            print(f"\nFolder: {folder}")
            for item in files:
                location = "reserv/" if item["is_reserv"] else ""
                print(f"  - File: {location}{item['file']} (Index: {item['index']})")
                print(f"    Expected SKUs: {item['expected_skus']}")
    else:
        print("\nSUCCESS: No remaining misclassified files found!")

if __name__ == "__main__":
    main()
