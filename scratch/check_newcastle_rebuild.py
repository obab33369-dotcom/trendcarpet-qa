import os
import re
import datetime
import json
import urllib.parse

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def get_beautiful_name(slug):
    words = slug.split('-')
    capitalized_words = [w.capitalize() for w in words if w]
    return " ".join(capitalized_words)

def clean_ref(filename):
    base = re.sub(r'^\d_+', '', filename)
    base, _ = os.path.splitext(base)
    return base

def normalize(name):
    return name.lower()

def resolve_anchor(ref):
    ref_lower = ref.lower()
    if 'newcastle' in ref_lower:
        return 'NEWCASTLE-BLACK', "Bokhylla Newcastle Svart"
    return None, ref

def main():
    import sys
    sys.path.append(WORKSPACE_DIR)
    from rebuild_all_by_time import load_db, resolve_anchor
    
    batch1 = load_db("rooms_turboflow_batch1.json")
    batch2 = load_db("rooms_turboflow_batch2.json")
    full_catalog = load_db("rooms_turboflow_full_catalog.json")
    
    # Let's search for files on OneDrive starting with prefix 3
    print("Files starting with 3 on OneDrive:")
    found_files = []
    for f in os.listdir(ONEDRIVE_DIR):
        if f.startswith("3-") and f.lower().endswith(('.png', '.jpg', '.jpeg')):
            found_files.append(f)
            
    print(found_files)
    
    # Let's see what references are in full_catalog[3]
    if 3 in full_catalog:
        print("\nReferences in prompt index 3:")
        print(full_catalog[3])
        for ref in full_catalog[3]["refs"]:
            sku, name = resolve_anchor(ref)
            print(f"  * Ref: {ref} -> SKU: {sku}, Name: {name}")

if __name__ == "__main__":
    main()
