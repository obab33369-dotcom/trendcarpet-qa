import os
import json

json_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\missed_products.json"

if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        missed_dict = json.load(f)
    
    target_skus = ["4100081", "4100071", "4100072", "1400041", "1400040", "3200459", "3100237", "1100476"]
    
    # Reverse map
    sku_to_name = {}
    for name, sku in missed_dict.items():
        sku_to_name[sku] = name
        
    print("SKU mapping in missed_products.json:")
    for sku in target_skus:
        name = sku_to_name.get(sku, "Not found")
        print(f"SKU: {sku} -> Name: {name}")
else:
    print("JSON not found")
