import os
import sys
import json

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reforma_pipeline.orchestrator import curate_sku

skus_to_check = [
    "37281105",
    "98875",
    "1200180",
    "99684",
    "91472",
    "0071_bäddsoffa-texas-beige",  # Let's see if this format works
    "0041_byrå-prime-6-lådor-valnöt-mässing"
]

print("CURATION INGESTION TEST:")
for sku in skus_to_check:
    print(f"\nChecking SKU: {sku}")
    res = curate_sku(sku)
    if res:
        prod_name, info, processed_slots = res
        print(f"  Prod Name: {prod_name}")
        print(f"  SKU info: {info.get('sku')}")
        print(f"  Slots found: {list(processed_slots.keys())}")
        for slot, slot_info in processed_slots.items():
            print(f"    Slot {slot}: {os.path.basename(slot_info['path'])} (is_studio: {slot_info['is_studio']}, is_zoom_view: {slot_info['is_zoom_view']}, has_white_bg: {slot_info.get('has_white_bg')})")
    else:
        print("  Failed to curate (SKU not in brand_sku_dict or no raw files).")
