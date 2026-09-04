import os

ORIG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]

skus = ["98235", "97828", "98237", "98236"]

print("--- SKU SEARCH RESULTS ---")
for sku in skus:
    print(f"\nSKU: {sku}")
    for folder in orig_folders:
        if sku in folder:
            print(f"  {folder}")
