import os
import json

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
dict_path = os.path.join(project_dir, "brand_sku_dict.json")

if os.path.exists(dict_path):
    with open(dict_path, "r", encoding="utf-8") as f:
        brand_sku_dict = json.load(f)
    for name, inf in brand_sku_dict.items():
        sku = inf['sku'].strip()
        if any(ts in sku for ts in ["19791", "1091", "WD2001", "WS-8651A"]):
            print(f"Product name: {name}")
            print(f"  SKU in dict: {sku}")
            print(f"  Info: {inf}")
else:
    print("Brand dict not found.")
