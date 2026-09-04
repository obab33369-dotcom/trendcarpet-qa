import sys
import os
import json

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from test_fixed_resolver import fixed_resolve_anchor, brand_sku_dict, sku_map

# We will read each line of the mismatches summary, and for each file listed,
# we will print exactly why it resolved to that SKU, and what its true SKU *should* be.

mismatches_file = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\fixed_mismatches_summary.txt"

if os.path.exists(mismatches_file):
    with open(mismatches_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print("Mismatches summary loaded.")
else:
    print("Error: mismatches file not found!")

# Let's inspect the resolved values for specific files:
files_to_check = [
    "2104_matta-velenna-svart-beige.jpg",
    "RG01-64.jpg",
    "2009_matta-arvella-brun-lila.jpg",
    
    "2014_matta-aureline-gron.jpg",
    "RG01-9.jpg",
    
    "2023_matta-carrano-svart-vit.jpg",
    "RG01-70.jpg",
    
    "2029_matta-cozy-luxury-gra-vit-160x230.jpg",
    "Pet-Pattern-160x230.jpg",
    
    "2040_matta-forma-beige.jpg",
    "RG01-33.jpg",
    
    "2047_matta-lorano-brun.jpg",
    "RG01-77.jpg",
    
    "2053_matta-marionae-brun-beige.jpg",
    "RG01-43.jpg",
    
    "2057_matta-markelo-gul-multi.jpg",
    "RG01-59.jpg",
    
    "2062_matta-merano-gra.jpg",
    "RG01-61.jpg",
    
    "2066_matta-molirae-brun-beige.jpg",
    "RG01-16.jpg",
    
    "2075_matta-rivetta-beige-gron.jpg",
    "RG01-37.jpg",
    
    "2079_matta-savelle-gron.jpg",
    "RG01-97.jpg",
    
    "2083_matta-savena-gul-gra.jpg",
    "RG01-22.jpg",
    
    "2100_matta-velenna-160x230-cm-ljusbrun-beige.jpg",
    "RG016.jpg",
    "2103_matta-velenna-200x280-cm-rod-beige.jpg",
    "RG019.jpg",
    
    "2107_matta-ventaro-beige.jpg",
    "RG01-89.jpg",
    
    "2113_matta-ventaro-rod-multi.jpg",
    "RG01-855.jpg"
]

print("\n=== VERIFYING RESOLVED SKUS ===")
for fn in files_to_check:
    sku, name = fixed_resolve_anchor(fn)
    # Check if there is a direct match in brand_sku_dict for this filename's slug
    # E.g. for "2014_matta-aureline-gron.jpg", the slug is "matta-aureline-gron"
    slug_part = fn.split('_')[-1].split('.')[0]
    info = brand_sku_dict.get(slug_part)
    correct_sku = info.get('sku') if info else "Unknown"
    correct_name = info.get('name') if info else "Unknown"
    
    if sku != correct_sku:
        print(f"File: {fn}")
        print(f"  Resolved to: SKU: {sku} | Name: {name}")
        print(f"  Correct info: SKU: {correct_sku} | Name: {correct_name}")
        print(f"  [STATUS]: RESOLVER ERROR!")
    else:
        print(f"File: {fn}")
        print(f"  Resolved correctly to: SKU: {sku} | Name: {name}")
        print(f"  [STATUS]: CORRECT RESOLUTION")
    print("-" * 50)
