import os

search_roots = [
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
]

print("=== SCANNING FOR CARRANO FILES ===")
for root in search_roots:
    for r, ds, fs in os.walk(root):
        for f in fs:
            if 'carrano' in f.lower() or 'rg01-71' in f.lower() or 'rg01-70' in f.lower() or 'rg01-72' in f.lower():
                print(f"File: {f} in {r}")
