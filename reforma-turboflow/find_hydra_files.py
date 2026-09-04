import os

search_keywords = ["3117", "hydra-3-hyllor-svart"]
root_dirs = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
]

for rdir in root_dirs:
    if not os.path.exists(rdir):
        continue
    for root, dirs, files in os.walk(rdir):
        for f in files:
            if any(kw in f.lower() for kw in search_keywords):
                print(f"FOUND: {os.path.join(root, f)}")
