import os

search_keyword = "t8049"
root_dirs = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
]

for rdir in root_dirs:
    if not os.path.exists(rdir):
        continue
    for root, dirs, files in os.walk(rdir):
        for f in files:
            if search_keyword in f.lower():
                print(f"FOUND: {os.path.join(root, f)}")
