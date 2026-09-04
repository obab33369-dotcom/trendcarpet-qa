import os

root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
terms = ["ponza", "gori", "eukalyptus", "mariana", "blavik", "kap verde", "fyra", "hydra"]

if os.path.exists(root_dir):
    print("Searching OneDrive Pictures...")
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            f_lower = f.lower()
            for t in terms:
                if t in f_lower:
                    rel_path = os.path.relpath(os.path.join(root, f), root_dir)
                    print(f"  MATCH [{t}]: {rel_path}")
else:
    print("OneDrive directory not found.")
