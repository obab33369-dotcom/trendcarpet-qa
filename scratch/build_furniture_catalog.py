import os
import json
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def get_sku(folder_name):
    m = re.search(r'\(([^)]+)\)', folder_name)
    if m:
        return m.group(1).strip()
    return None

def main():
    if not os.path.exists(CLEAN_ROOT):
        print("Clean root does not exist.")
        return
        
    folders = sorted([d for d in os.listdir(CLEAN_ROOT) if os.path.isdir(os.path.join(CLEAN_ROOT, d))])
    catalog = {}
    
    for folder in folders:
        if is_carpet(folder):
            continue
            
        sku = get_sku(folder)
        if sku:
            ref_path = None
            folder_path = os.path.join(CLEAN_ROOT, folder)
            for f in os.listdir(folder_path):
                if f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    ref_path = os.path.join(folder_path, f)
                    break
            
            catalog[sku] = {
                "folder_name": folder,
                "ref_path": ref_path
            }
            
    project_catalog_path = os.path.join(PROJECT_DIR, "scratch", "furniture_catalog.json")
    with open(project_catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        
    print(f"Furniture catalog built with {len(catalog)} products and saved to {project_catalog_path}")

if __name__ == "__main__":
    main()
