import os
import sys
import json

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
sys.path.append(project_dir)

from reforma_pipeline.orchestrator import curate_sku

test_skus = [
    "WS-8651A-BlackBlack-NEW",
    "WD2001-KD-white",
    "19791-black-oak",
    "19791-walnut",
    "1091-white-pigmented"
]

for sku in test_skus:
    print(f"\nCurating SKU: {sku}...")
    res = curate_sku(sku)
    if res is None:
        print("  Failed to curate.")
    else:
        prod_name, info, processed_slots = res
        print(f"  Product: {prod_name}")
        for slot, img_info in processed_slots.items():
            print(f"    Slot {slot}: {img_info['path']}")
