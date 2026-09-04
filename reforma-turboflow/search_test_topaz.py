import os

path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
if os.path.exists(path):
    print(f"Files in {path}: {len(os.listdir(path))}")
    for f in os.listdir(path):
        if "t8049" in f.lower() or "portofino" in f.lower() or "capri" in f.lower():
            print(f"  {f}")
else:
    print("Path does not exist")
