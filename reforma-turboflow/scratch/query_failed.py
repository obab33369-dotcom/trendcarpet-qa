import json

with open("brand_sku_dict.json", "r", encoding="utf-8") as f:
    db = json.load(f)

failed_skus = [s.lower() for s in [
    'matgrupp17', 'matgrupp23', 'matgrupp26', 'matgrupp28', 'matgrupp30', 
    'matgrupp33', 'matgrupp36', 'matgrupp39', 'matgrupp51', 'matgrupp6', 
    'matgrupp7', 'H000021092', 'MG1505', 'MLM-502390', 'NOVASU02'
]]

for slug, info in db.items():
    sku = info.get("sku", "").strip().lower()
    if sku in failed_skus:
        print(f"SKU: {info.get('sku')} | Name: '{info.get('name')}' | DB Cat: {info.get('category')}")
