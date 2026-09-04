import os
import json
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")

def get_sku(folder_name):
    m = re.search(r'\(([^)]+)\)', folder_name)
    if m:
        return m.group(1).strip()
    return None

def main():
    folders = sorted([d for d in os.listdir(CLEAN_ROOT) if os.path.isdir(os.path.join(CLEAN_ROOT, d))])
    catalog = {}
    
    for folder in folders:
        sku = get_sku(folder)
        if sku:
            ref_path = None
            for f in os.listdir(os.path.join(CLEAN_ROOT, folder)):
                if f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    ref_path = os.path.join(CLEAN_ROOT, folder, f)
                    break
            
            catalog[sku] = {
                "folder_name": folder,
                "ref_path": ref_path
            }
            
    catalog_path = os.path.join(ONEDRIVE_DIR, "..", "carpet_catalog.json") # Save outside or in project scratch
    project_catalog_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\carpet_catalog.json"
    
    with open(project_catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        
    print(f"Catalog built with {len(catalog)} products and saved to {project_catalog_path}")

if __name__ == "__main__":
    main()
