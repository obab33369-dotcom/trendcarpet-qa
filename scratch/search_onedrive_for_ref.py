import os

PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
targets = [
    "2008_matta-aravelle-turkos-multi",
    "2011_matta-arvella-rod-gron",
    "2012_matta-aureline-beige-brun",
    "2013_matta-aureline-beige-gra",
    "2014_matta-aureline-gron",
    "2016_matta-avendo-rod",
    "2017_matta-belden-gron",
    "2020_matta-calvera-rod",
    "2021_matta-carrano-brun-vit",
    "2087_matta-seronis-svart-beige",
    "2089_matta-sorvento-svart-beige",
    "2104_matta-velenna-svart-beige"
]

print("Searching Pictures directory for carpet reference files:")
found_count = 0
if os.path.exists(PICTURES_DIR):
    for root, dirs, files in os.walk(PICTURES_DIR):
        for f in files:
            name, ext = os.path.splitext(f)
            for target in targets:
                if target in name:
                    print(f"  Found: {os.path.join(root, f)}")
                    found_count += 1
    print(f"Total found: {found_count}")
else:
    print(f"Directory does not exist: {PICTURES_DIR}")
