import os

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
clean_dir = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")

target_fn = "023-architectural-digest-style-023 (1).png"
found_paths = []

if os.path.exists(clean_dir):
    for root, dirs, files in os.walk(clean_dir):
        for f in files:
            if f == target_fn:
                found_paths.append(os.path.join(root, f))

print(f"Found {len(found_paths)} occurrences of {target_fn}:")
for p in found_paths:
    print(f"  - {p}")
