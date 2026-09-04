import os
import sys
import json

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
sys.path.insert(0, project_dir)

from reforma_pipeline.orchestrator import curate_sku

test_skus = [
    "WS-8651A-BlackBlack-NEW",
    "WD2001-KD-white",
    "19791-black-oak",
    "19791-walnut",
    "1091-white-pigmented"
]

print("Ingested source file paths for target SKUs:")
for sku in test_skus:
    res = curate_sku(sku)
    if res:
        prod_name, info, processed_slots = res
        print(f"\nSKU: {sku} (Name: {prod_name})")
        for slot, img_info in sorted(processed_slots.items()):
            print(f"  Slot {slot}: {img_info['path']} (is_studio={img_info['is_studio']}, is_zoom={img_info['is_zoom_view']})")
    else:
        print(f"\nSKU {sku} not found during curation.")
