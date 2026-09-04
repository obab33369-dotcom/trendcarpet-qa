import json
import os
import re
import urllib.parse

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
prompt_db_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'rooms_turboflow_full_catalog.json')

# Load the prompt database
with open(prompt_db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

db_by_index = {}
for item in db:
    prompt_text = item.get("prompt", "")
    m = re.match(r"^(\d+)\s*-\s*", prompt_text)
    if m:
        idx = int(m.group(1))
        db_by_index[idx] = item

print(f"Loaded {len(db_by_index)} prompt configurations.")

# The 21 flagged folders
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

# We want to check both destinations:
# 1. Reforma-Full-Catalog-sortering
# 2. Reforma-Mattor-sortering
# And also look at Reforma-Full-Catalog-sortering-borttagna or similar if they were moved there.

search_roots = [
    os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering"),
    os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering-borttagna"),
    os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering"),
    os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering-borttagna"),
]

print("\nTracing flagged folders:")
for folder_name in flagged_folders:
    print("=" * 80)
    print(f"FOLDER: {folder_name}")
    
    # Let's find all render files that were copied to this folder
    found_files = []
    for root in search_roots:
        p = os.path.join(root, folder_name)
        if os.path.exists(p):
            # scan files in p (and subfolders like reserv)
            for r, ds, fs in os.walk(p):
                for f in fs:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                        found_files.append((f, os.path.join(r, f)))
                        
    if not found_files:
        print("  No render files found on disk for this folder.")
        # Try to guess SKU from folder name
        m_sku = re.search(r'\(([^)]+)\)$', folder_name)
        if m_sku:
            sku = m_sku.group(1).strip()
            print(f"  Guessed SKU from folder name: {sku}")
            # Find in DB where this SKU is listed as reference
            db_matches = []
            for idx, item in db_by_index.items():
                refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
                for ref in refs:
                    if sku.lower() in ref.lower():
                        db_matches.append((idx, ref, item.get('prompt', '')))
            if db_matches:
                print(f"  Found {len(db_matches)} indices in DB mentioning this SKU in refs:")
                for idx, ref, prompt in db_matches[:5]:
                    print(f"    Index {idx}: Ref={ref} | Prompt: {prompt[:120]}")
                if len(db_matches) > 5:
                    print(f"    ... and {len(db_matches)-5} more.")
        continue
        
    print(f"  Found {len(found_files)} render files on disk:")
    for fn, full_path in found_files:
        m_idx = re.match(r"^(\d+)", fn)
        if m_idx:
            idx = int(m_idx.group(1))
            print(f"  - File: {fn}")
            if idx in db_by_index:
                item = db_by_index[idx]
                print(f"    Prompt: {item.get('prompt', '')}")
                print(f"    Refs  : {item.get('image_references', '')}")
            else:
                print(f"    Index {idx} not found in prompt database.")
        else:
            print(f"  - File: {fn} (no numeric prefix found)")
