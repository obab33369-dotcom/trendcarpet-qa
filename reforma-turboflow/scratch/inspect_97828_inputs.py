import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reforma_pipeline.classification import classify_and_size_product, adjust_size_by_name

prod_name = "stol-angom-beige"
category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)

print(f"Product: {prod_name}")
print(f"Category: {category}")
print(f"Targets: w={target_w}, h={target_h}, floor_pct={floor_pct}, is_centered={is_centered}")
