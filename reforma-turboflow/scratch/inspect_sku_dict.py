import json
with open("brand_sku_dict.json", "r", encoding="utf-8") as f:
    brand_sku_dict = json.load(f)

print("Total SKUs in brand_sku_dict.json:", len(brand_sku_dict))
print("First 20 items:")
for i, (name, info) in enumerate(list(brand_sku_dict.items())[:20]):
    print(f"Name: {name} -> SKU: {info.get('sku')} | url: {info.get('url')}")
