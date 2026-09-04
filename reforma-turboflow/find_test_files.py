import os

topaz_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
files = os.listdir(topaz_dir)
matches = [f for f in files if "stol-alta" in f.lower() or "stol-ask" in f.lower()]
print("Matching files:")
for f in matches[:20]:
    print("  ", f)
print(f"Total matching: {len(matches)}")
