import os
import re
import datetime
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    import sys
    sys.path.append(WORKSPACE_DIR)
    from rebuild_all_by_time import load_db, resolve_anchor
    
    # Load database
    full_catalog = load_db("rooms_turboflow_full_catalog.json")
    
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
    
    # Map them to NEWCASTLE-BLACK
    primaries = []
    secondaries = []
    
    for item in full_catalog_files:
        prefix = item["prefix"]
        fn = item["filename"]
        
        if prefix in full_catalog:
            refs = full_catalog[prefix]["refs"]
            for ref_idx, ref in enumerate(refs):
                sku, name = resolve_anchor(ref)
                if sku == "NEWCASTLE-BLACK":
                    if ref_idx == 0:
                        primaries.append(item)
                    else:
                        secondaries.append(item)
                        
    print(f"NEWCASTLE-BLACK in Full Catalog run:")
    print(f"  * Primaries count: {len(primaries)}")
    print(f"  * Secondaries count: {len(secondaries)}")
    
    print("\nPrimaries details:")
    for p in primaries:
        print(f"    - {p['filename']} (mtime: {p['mtime']})")
        
    print("\nSecondaries details (first 10):")
    for s in secondaries[:10]:
        print(f"    - {s['filename']} (mtime: {s['mtime']})")

if __name__ == "__main__":
    main()
