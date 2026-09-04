import json
import os

for jf in ["brand_sku_dict.json", "furniture_db.json", "furniture_db_batch2.json", "furniture_db_batch3.json"]:
    if os.path.exists(jf):
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in data:
            if "bokhylla-hydra-3-hyllor-svart" in k.lower():
                print(f"File: {jf}, key: {k}")
            if "fatolj-portofino-beige-boucle" in k.lower():
                print(f"File: {jf}, key: {k}")
