import sys
import os
from PIL import Image

# Add reforma-turboflow to path so we can import find_original_source_image
sys.path.append(r"c:\Users\AndronikLindgren\\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
from vision_auto_corrector import find_original_source_image, classify_and_size_product, CATEGORY_TARGETS

sku = '19791'
prod_name = "Stol 'Ystad' - NaturSvart"

src = find_original_source_image(sku, prod_name, slot=1)
print(f"find_original_source_image('{sku}', '{prod_name}') returned: {src}")

if src and os.path.exists(src):
    try:
        with Image.open(src) as img:
            print(f"Source size: {img.size}")
    except Exception as e:
        print(f"Error opening source: {e}")
else:
    print("Source path does not exist.")

# Also check for 19791-black-oak
sku_bo = '19791-black-oak'
prod_name_bo = "Stol 'Ystad' - SvartGrå"
src_bo = find_original_source_image(sku_bo, prod_name_bo, slot=1)
print(f"\nfind_original_source_image('{sku_bo}', '{prod_name_bo}') returned: {src_bo}")

if src_bo and os.path.exists(src_bo):
    try:
        with Image.open(src_bo) as img:
            print(f"Source size: {img.size}")
    except Exception as e:
        print(f"Error opening source: {e}")
else:
    print("Source path does not exist.")
