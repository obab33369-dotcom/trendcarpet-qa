import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
prompt_db_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'rooms_turboflow_full_catalog.json')
carpet_catalog_path = os.path.join(WORKSPACE_DIR, 'scratch', 'carpet_catalog.json')
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

with open(prompt_db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

with open(carpet_catalog_path, "r", encoding="utf-8") as f:
    carpet_catalog = json.load(f)

with open(sku_map_path, "r", encoding="utf-8") as f:
    sku_map = json.load(f)

with open(brand_dict_path, "r", encoding="utf-8") as f:
    brand_sku_dict = json.load(f)

db_by_index = {int(re.match(r"^(\d+)", item.get("prompt", "")).group(1)): item for item in db if re.match(r"^(\d+)", item.get("prompt", ""))}

# Import the resolve_anchor from execute_full_catalog_sorting.py
import sys
sys.path.append(os.path.join(WORKSPACE_DIR, 'scratch'))
from execute_full_catalog_sorting import resolve_anchor

flagged_folders = [
    "Matta Aravelle - Multi (RG01-20)",
    "Matta Arvella - RödGrön (RG01-65)",
    "Matta Aureline - BeigeBrun (RG01-8)",
    "Matta Aureline - Grön (RG01-9)",
    "Matta Aureline BeigeGrå (RG01-7)",
    "Matta Avendo - GulBeige (RG01-76)",
    "Matta Avendo - Röd (RG01-75)",
    "Matta Belden - Grön (RG01-74)",
    "Matta Belden - Röd (RG01-73)",
    "Matta Calvera - Grå (RG01-35)",
    "Matta Calvera - Röd (RG01-34)",
    "Matta Carrano - GråVit (RG01-72)",
    "Matta Carrano - Grön (RG01-71)",
    "Matta Carrano - SvartVit (RG01-70)",
    "Matta Ventaro - GrönGul (RG01-91)",
    "Matta Ventaro - Multi (RG01-87)",
    "Matta Ventaro - RosaBrun (RG01-90)",
    "Matta Ängelholm - GråBlå (RG002)",
    "Matta Ängelholm - Grön (RG00)",
    "Matta Ängelholm - Mörkbrun (RG001)",
    "Ryamatta Aranga Super Soft Fur Rosa (H100017)"
]

search_roots = [
    os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering"),
    os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering-borttagna"),
    os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering"),
    os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering-borttagna"),
]

output_lines = []

for folder_name in flagged_folders:
    output_lines.append("=" * 100)
    output_lines.append(f"FOLDER: {folder_name}")
    
    # Try to guess SKU from folder name
    m_sku = re.search(r'\(([^)]+)\)$', folder_name)
    expected_sku = m_sku.group(1).strip() if m_sku else None
    output_lines.append(f"Expected SKU in this folder: {expected_sku}")
    
    # Scan files in both clean and borttagna directories
    found_files = []
    for root in search_roots:
        p = os.path.join(root, folder_name)
        if os.path.exists(p):
            for r, ds, fs in os.walk(p):
                for f in fs:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                        found_files.append((f, os.path.basename(root)))
                        
    if not found_files:
        output_lines.append("  No files found on disk for this folder.")
        continue
        
    output_lines.append(f"  Found {len(found_files)} files on disk:")
    
    # Group files by index
    for fn, root_name in found_files:
        m_idx = re.match(r"^(\d+)", fn)
        if not m_idx:
            output_lines.append(f"    - File: {fn} (no numeric prefix) in {root_name}")
            continue
        idx = int(m_idx.group(1))
        output_lines.append(f"    - File: {fn} (Index {idx}) in {root_name}")
        
        if idx in db_by_index:
            item = db_by_index[idx]
            prompt_text = item.get("prompt", "")
            refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
            
            output_lines.append(f"      Prompt: {prompt_text[:200]}...")
            output_lines.append(f"      Image Refs: {refs}")
            
            # Show resolved SKUs for each image ref
            resolved_skus = []
            for ref in refs:
                res_sku, res_name = resolve_anchor(ref)
                resolved_skus.append((ref, res_sku, res_name))
            output_lines.append("      Resolved SKUs:")
            for ref, res_sku, res_name in resolved_skus:
                output_lines.append(f"        * {ref} -> SKU: {res_sku} ({res_name})")
        else:
            output_lines.append(f"      Index {idx} NOT found in prompt database!")

with open(os.path.join(WORKSPACE_DIR, "scratch", "carpet_debug_details.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("Debug details compiled and written to scratch/carpet_debug_details.txt.")
