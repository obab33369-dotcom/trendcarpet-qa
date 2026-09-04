import os
import re
import datetime
import shutil
import urllib.parse
import stat

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def resolve_anchor_fixed(ref):
    ref_lower = ref.lower()
    if 'newcastle' in ref_lower:
        return 'NEWCASTLE-BLACK', "Bokhylla Newcastle Svart"
    if 'cardoba' in ref_lower:
        return 'H000022821', "Sidobord Cardoba Natur"
    if 'istria' in ref_lower:
        return '76375', "Sängbord Istria Natur"
    if 'blåvik' in ref_lower or 'blavik' in ref_lower:
        return '23101-natur', "Byrå Blåvik - Natur"
    if 'cadiz-natur' in ref_lower and 'skrivbord' in ref_lower:
        return 'CADIZ-DESK', "Skrivbord Cadiz - Natur"
    if 'torekov' in ref_lower:
        if 'valnöt' in ref_lower or 'valnot' in ref_lower:
            return '2251-1 Walnut', "Sidobord Torekov - Ljus Valnöt"
        elif 'ek' in ref_lower:
            return '2251-1 Oak', "Sidobord Torekov Ek"
        elif 'skåp' in ref_lower or 'skap' in ref_lower or 'natur' in ref_lower:
            return 'TOREKOV-CABINET', "Skåp Torekov - Natur"
    return None, None

def find_reference_photo_everywhere(sku):
    # Search for reference images of the SKU in other folders on OneDrive
    unquoted_sku = urllib.parse.unquote(sku)
    for root, dirs, files in os.walk(ONEDRIVE_DIR):
        # Skip current clean root to avoid finding nothing
        if "Reforma-Full-Catalog-sortering" in root and sku not in root:
            continue
        for f in files:
            if f.startswith("00_REFERENCE_") and unquoted_sku.lower() in f.lower():
                return os.path.join(root, f)
            if f.lower() == f"{unquoted_sku.lower()}.jpg" or f.lower() == f"{unquoted_sku.lower()}.png":
                return os.path.join(root, f)
                
    # Check in reforma-original-images
    orig_dir = os.path.join(WORKSPACE_DIR, "reforma-original-images")
    if os.path.exists(orig_dir):
        for f in os.listdir(orig_dir):
            if unquoted_sku.lower() in f.lower():
                return os.path.join(orig_dir, f)
                
    return None

def main():
    print("=== RESTORING ACCIDENTALLY DELETED FURNITURE FOLDERS ===")
    
    import sys
    sys.path.append(WORKSPACE_DIR)
    from rebuild_all_by_time import load_db, clean_folder_name
    
    # 1. Load full catalog prompts database
    full_catalog = load_db("rooms_turboflow_full_catalog.json")
    
    # Target folders info
    target_skus = {
        'NEWCASTLE-BLACK': "Bokhylla Newcastle Svart (NEWCASTLE-BLACK)",
        '23101-natur': "Byrå Blåvik - Natur (23101-natur)",
        'H000022821': "Sidobord Cardoba Natur (H000022821)",
        '2251-1 Walnut': "Sidobord Torekov - Ljus Valnöt (2251-1 Walnut)"
    }
    
    # 2. Scan all files in turboflow root & square subfolders to find matching renders
    dirs_to_scan = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    full_catalog_files = []
    for d in dirs_to_scan:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            m = re.match(r"^(\d+)", f)
            if not m:
                continue
            prefix = int(m.group(1))
            
            if 1 <= prefix <= 3340:
                path = os.path.join(d, f)
                try:
                    stat = os.stat(path)
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                    
                    is_full_catalog = False
                    if "(1)" in f or " (1)" in f:
                        is_full_catalog = True
                    elif mtime.date() >= datetime.date(2026, 6, 8):
                        is_full_catalog = True
                        
                    if is_full_catalog:
                        full_catalog_files.append({
                            "filename": f,
                            "prefix": prefix,
                            "path": path,
                            "mtime": mtime
                        })
                except Exception:
                    pass
                    
    print(f"Isolated {len(full_catalog_files)} files belonging to the Full Catalog run.")
    
    # 3. Map files to target SKUs
    primaries = {sku: [] for sku in target_skus}
    secondaries = {sku: [] for sku in target_skus}
    
    for item in full_catalog_files:
        prefix = item["prefix"]
        if prefix in full_catalog:
            refs = full_catalog[prefix]["refs"]
            for ref_idx, ref in enumerate(refs):
                sku, name = resolve_anchor_fixed(ref)
                if sku in target_skus:
                    if ref_idx == 0:
                        primaries[sku].append(item)
                    else:
                        secondaries[sku].append(item)
                        
    # 4. Rebuild folders and copy files
    copied_total = 0
    ref_copied_total = 0
    
    for sku, folder_name in target_skus.items():
        clean_name = clean_folder_name(folder_name)
        product_folder = os.path.join(CLEAN_ROOT, clean_name)
        os.makedirs(product_folder, exist_ok=True)
        make_writable(product_folder)
        
        print(f"\nProcessing {folder_name} (SKU: {sku}):")
        
        # Copy primary files
        primary_count = 0
        seen_primary = set()
        for p in primaries[sku]:
            if p["filename"] not in seen_primary:
                seen_primary.add(p["filename"])
                dest = os.path.join(product_folder, p["filename"])
                try:
                    if os.path.exists(dest):
                        make_writable(dest)
                        os.remove(dest)
                    shutil.copy2(p["path"], dest)
                    primary_count += 1
                    copied_total += 1
                except Exception as e:
                    print(f"  Failed to copy primary {p['filename']}: {e}")
        print(f"  Copied {primary_count} primary files to main folder.")
        
        # Copy secondary files
        secondary_count = 0
        seen_secondary = set()
        if secondaries[sku]:
            reserv_folder = os.path.join(product_folder, "reserv")
            os.makedirs(reserv_folder, exist_ok=True)
            make_writable(reserv_folder)
            
            for s in secondaries[sku]:
                if s["filename"] not in seen_secondary:
                    seen_secondary.add(s["filename"])
                    dest = os.path.join(reserv_folder, s["filename"])
                    try:
                        if os.path.exists(dest):
                            make_writable(dest)
                            os.remove(dest)
                        shutil.copy2(s["path"], dest)
                        secondary_count += 1
                        copied_total += 1
                    except Exception as e:
                        print(f"  Failed to copy secondary {s['filename']}: {e}")
        print(f"  Copied {secondary_count} secondary files to reserv folder.")
        
        # Find and copy reference photo
        ref_src = find_reference_photo_everywhere(sku)
        if ref_src:
            ext = os.path.splitext(ref_src)[1]
            dest_ref = os.path.join(product_folder, f"00_REFERENCE_{sku}{ext}")
            try:
                if os.path.exists(dest_ref):
                    make_writable(dest_ref)
                    os.remove(dest_ref)
                shutil.copy2(ref_src, dest_ref)
                print(f"  Copied reference photo from: {os.path.relpath(ref_src, ONEDRIVE_DIR)}")
                ref_copied_total += 1
            except Exception as e:
                print(f"  Failed to copy reference photo {ref_src}: {e}")
        else:
            print("  No reference photo found!")
            
    print(f"\nRestore finished! Successfully copied {copied_total} renders and {ref_copied_total} reference photos.")

if __name__ == "__main__":
    main()
