import os
import glob

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

csv_files = glob.glob(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "*.csv"))

def search_csv(filepath, text):
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(';')
        for line in f:
            if text.lower() in line.lower():
                parts = line.strip().split(';')
                if len(parts) >= len(header):
                    row_dict = dict(zip(header, parts))
                    results.append(row_dict)
    return results

for csv_path in csv_files:
    print(f"\n=== Searching in {os.path.basename(csv_path)} ===")
    matches = search_csv(csv_path, "texas") + search_csv(csv_path, "lucca")
    # Deduplicate
    seen = set()
    unique_matches = []
    for m in matches:
        k = (m.get("Row Number"), m.get("Package ID"))
        if k not in seen:
            seen.add(k)
            unique_matches.append(m)
            
    print(f"Total matches: {len(unique_matches)}")
    for m in unique_matches[:5]:
        row_num = m.get('Row Number') or m.get('Row') or list(m.values())[0]
        pkg_id = m.get('Package ID') or m.get('Package') or ''
        focus_desc = m.get('Focus Description') or m.get('Description') or ''
        refs_util = m.get('References Utilized') or m.get('References') or ''
        print(f"  Row: {row_num} | Pkg: {pkg_id} | Focus: {str(focus_desc)[:80]}")
        print(f"    Refs: {refs_util}")
