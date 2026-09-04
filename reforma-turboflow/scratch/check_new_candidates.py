import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set IGNORE_FIX_FOLDER=1 to source strictly from Topaz/Fallback
os.environ["IGNORE_FIX_FOLDER"] = "1"
from reforma_pipeline.orchestrator import curate_sku

skus = ["67099", "67100", "1400034", "H000017689", "2300103"]

for sku in skus:
    res = curate_sku(sku)
    if res:
        prod_name, info, processed_slots = res
        print(f"\nSKU: {sku} -> Prod: {prod_name}")
        for slot, slot_info in processed_slots.items():
            print(f"  Slot {slot}: {os.path.basename(slot_info['path'])} | is_studio: {slot_info['is_studio']}, is_zoom_view: {slot_info['is_zoom_view']}")
    else:
        print(f"\nSKU {sku} curation FAILED")
