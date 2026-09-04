import os
import glob

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
csv_files = glob.glob(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "*.csv"))

def search_texas_in_csv(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline().strip().split(';')
        for idx, line in enumerate(f):
            if "texas" in line.lower() or "lucca" in line.lower():
                parts = line.strip().split(';')
                results.append((idx + 2, parts))
    return header, results

for csv_path in csv_files:
    header, matches = search_texas_in_csv(csv_path)
    if matches:
        print(f"\n=== Mapped references in {os.path.basename(csv_path)} (Found {len(matches)} rows) ===")
        for line_no, parts in matches[:10]:
            if len(parts) >= len(header):
                row_dict = dict(zip(header, parts))
                print(f"  Line {line_no} | Row {row_dict.get('Row Number') or row_dict.get('Row')} | Seating: {row_dict.get('Seating Product')}")
                print(f"    Refs: {row_dict.get('References Utilized')}")
            else:
                print(f"  Line {line_no}: {'; '.join(parts[:5])}...")
