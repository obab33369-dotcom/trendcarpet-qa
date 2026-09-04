import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
target_file = "2218-architectural-digest-styl-105.png"

print("=== CLEAN LOCATIONS ===")
for root, dirs, files in os.walk(CLEAN_DIR):
    if target_file in files:
        print(f"  - {os.path.join(root, target_file)}")
        
print("\n=== DISCARD LOCATIONS ===")
for root, dirs, files in os.walk(DISCARD_DIR):
    if target_file in files:
        print(f"  - {os.path.join(root, target_file)}")
