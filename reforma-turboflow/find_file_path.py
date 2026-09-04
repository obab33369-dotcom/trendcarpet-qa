import os

search_filename = "2048_matta-lorano-rod.jpg"
root_dirs = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
]

found = False
for rdir in root_dirs:
    if not os.path.exists(rdir):
        continue
    for root, dirs, files in os.walk(rdir):
        for f in files:
            if f.lower() == search_filename.lower():
                print(f"FOUND: {os.path.join(root, f)}")
                found = True

if not found:
    print("Could not find file anywhere in specified roots.")
