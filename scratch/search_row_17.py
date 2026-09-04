import os
import glob

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

csv_files = glob.glob(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "*.csv"))

rows_to_find = ["17", "23", "33", "637", "1241", "1845"]

for csv_path in csv_files:
    print(f"\n================ SEARCHING IN {os.path.basename(csv_path)} ================")
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline().strip().split(';')
        for line in f:
            parts = line.strip().split(';')
            if parts and parts[0] in rows_to_find:
                print(f"Row {parts[0]}:")
                if len(parts) >= len(header):
                    row_dict = dict(zip(header, parts))
                    print(f"  Focus: {row_dict.get('Focus Description')}")
                    print(f"  Table: {row_dict.get('Table Product')} | Seating: {row_dict.get('Seating Product')}")
                    print(f"  Refs: {row_dict.get('References Utilized')}")
                else:
                    print(f"  Raw: {line.strip()[:180]}")
