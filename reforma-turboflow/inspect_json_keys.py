import json

json_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\missed_products.json"
with open(json_path, "r", encoding="utf-8") as f:
    missed_dict = json.load(f)

print("Missed products matching 77415 or 82563:")
for k, v in missed_dict.items():
    if "77415" in k or "77415" in v or "82563" in k or "82563" in v:
        print(f"  Key: {k} -> Value: {v}")
