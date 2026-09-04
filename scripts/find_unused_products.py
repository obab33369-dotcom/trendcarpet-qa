import os
import json
import re

TEST_TOPAZ = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
USED_DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"

def parse_category(fname):
    fname = fname.lower()
    if 'barstol' in fname:
        return 'stol'
    elif 'stol' in fname or 'fåtölj' in fname or 'soff' in fname or 'bänk' in fname or 'pall' in fname:
        return 'stol'
    elif 'soffbord' in fname or 'avlastningsbord' in fname or 'matbord' in fname or 'klaffbord' in fname or 'barbord' in fname or 'skrivbord' in fname or 'bord' in fname:
        return 'bord'
    elif 'matta' in fname:
        return 'matta'
    elif any(x in fname for x in ['bokhylla', 'skåp', 'byrå', 'hylla', 'tv-bänk', 'skänk', 'sideboard', 'mediabänk', 'garderob']):
        return 'förvaring'
    elif 'lampa' in fname:
        return 'lampa'
    else:
        return 'andra'

def find_unused():
    if not os.path.exists(TEST_TOPAZ) or not os.path.exists(USED_DB_PATH):
        print("Required folders/files are missing.")
        return
        
    # Load used products
    with open(USED_DB_PATH, "r", encoding="utf-8") as f:
        used_db = json.load(f)
        
    used_ids = set()
    for k in used_db.keys():
        parts = k.split('_', 1)
        if len(parts) >= 1:
            # Get 4-digit ID
            used_ids.add(parts[0])
            
    print(f"Used product IDs in first batch: {len(used_ids)}")
    
    # Scan TEST TOPAZ for primary webp files
    all_files = os.listdir(TEST_TOPAZ)
    primary_files = []
    
    for f in all_files:
        if f.lower().endswith('.webp'):
            # Must match primary pattern (starts with digits, has -1-)
            # E.g. '0001_lampa-senigallia-m-vit-svart-1-26U-wonder.webp'
            if '-1-' in f.lower() or '-1-26u-wonder' in f.lower():
                match = re.match(r'^(\d+)_', f)
                if match:
                    primary_files.append(f)
                    
    print(f"Total primary files in master: {len(primary_files)}")
    
    # Filter unused
    unused_files = []
    unused_ids = set()
    
    for f in primary_files:
        match = re.match(r'^(\d+)_', f)
        item_id = match.group(1)
        if item_id not in used_ids:
            unused_files.append(f)
            unused_ids.add(item_id)
            
    print(f"Total fresh, unused product IDs: {len(unused_ids)} ({len(unused_files)} files)")
    
    # Category breakdown of unused
    cat_breakdown = {}
    for f in unused_files:
        cat = parse_category(f)
        cat_breakdown[cat] = cat_breakdown.get(cat, 0) + 1
        
    print("\nCategory breakdown of unused products:")
    for cat, count in sorted(cat_breakdown.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {cat.capitalize()}: {count} files")
        
if __name__ == "__main__":
    find_unused()
