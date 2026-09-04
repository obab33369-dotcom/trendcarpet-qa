import numpy as np
from PIL import Image
import os

images = [
    ("chair_0", "test_new_pipeline_chair_armchair_0.jpg"),
    ("chair_1", "test_new_pipeline_chair_armchair_1.jpg"),
    ("sofa_0", "test_new_pipeline_sofa_0.jpg"),
    ("sofa_1", "test_new_pipeline_sofa_1.jpg"),
    ("table_0", "test_new_pipeline_table_non_dining_0.jpg"),
    ("table_1", "test_new_pipeline_table_non_dining_1.jpg")
]

for name, filename in images:
    if os.path.exists(filename):
        with Image.open(filename) as img:
            arr = np.array(img.convert("L"))
            # Detect product pixels (thresholding at < 254 to be safe)
            prod_y, prod_x = np.argwhere(arr < 254).T
            if prod_y.size > 0:
                y_min, y_max = prod_y.min(), prod_y.max()
                x_min, x_max = prod_x.min(), prod_x.max()
                w = x_max - x_min + 1
                h = y_max - y_min + 1
                print(f"{name} ({filename}):")
                print(f"  Bounding box: y_min={y_min}, y_max={y_max}, x_min={x_min}, x_max={x_max}")
                print(f"  Width={w} ({w/1000*100:.1f}%), Height={h} ({h/1000*100:.1f}%)")
                print(f"  Floor level (y_max) = {y_max} (distance from bottom = {1000 - y_max - 1}px, {1000 - y_max - 1}% from bottom)")
            else:
                print(f"{name} ({filename}): No product detected (fully white?)")
    else:
        print(f"{name} ({filename}): File not found")
