import csv
import os

csv_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-original-images\brand_sku_map.csv"

if os.path.exists(csv_path):
    print(f"Searching {csv_path}...")
    keywords = ["hydra", "montmartre", "oslo", "angom", "san francisco", "texas"]
    
    with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        print(f"Header: {header}")
        
        matches = {kw: [] for kw in keywords}
        for row in reader:
            row_str = " | ".join(row).lower()
            for kw in keywords:
                if kw in row_str:
                    matches[kw].append(row)
                    
    for kw, rows in matches.items():
        print(f"\nKeyword: {kw} (Found {len(rows)} matches)")
        for r in rows[:20]:
            print(f"  {r}")
        if len(rows) > 20:
            print(f"  ... and {len(rows) - 20} more rows")
else:
    print("CSV file not found.")
