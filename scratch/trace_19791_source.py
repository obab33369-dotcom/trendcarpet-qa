import os
import sys
import json

REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
sys.path.append(REFORMA_DIR)
import vision_auto_corrector as vac

sku = "19791"
prod_name = "Stol 'Ystad' - Natur/Svart"
src_image = vac.find_original_source_image(sku, prod_name, slot=1)

print(f"Source Image path: {src_image}")
if src_image and os.path.exists(src_image):
    print(f"Exists! Size: {os.path.getsize(src_image)} bytes")
else:
    print("Source image does not exist or was not found!")
