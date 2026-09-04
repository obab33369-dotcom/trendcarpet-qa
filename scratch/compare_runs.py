import os
import sys
import numpy as np
import json
from PIL import Image

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
from reforma_pipeline.orchestrator import curate_sku, process_sku_cpu_worker, load_bbox_db

os.environ["FORCE_ORIGINAL"] = "1"
os.environ["IGNORE_FIX_FOLDER"] = "1"

sku = "37281105"
curated = curate_sku(sku)
print("Curated:", curated is not None)

bbox_db = load_bbox_db()
artiklar_dir = "scratch/test_out/artiklar"
liten_dir = "scratch/test_out/artiklar/liten"
zoom_dir = "scratch/test_out/artiklar/zoom"

os.makedirs(artiklar_dir, exist_ok=True)
os.makedirs(liten_dir, exist_ok=True)
os.makedirs(zoom_dir, exist_ok=True)

task = (curated[0], curated[1], curated[2], bbox_db, artiklar_dir, liten_dir, zoom_dir)
sku_clean, results = process_sku_cpu_worker(task)
print("Results:", results)

# Check Zoom1 output in scratch
out_path = os.path.join(zoom_dir, "37281105_1.jpg")
if os.path.exists(out_path):
    img = Image.open(out_path)
    arr = np.array(img)
    print("Scratch Output Size:", img.size)
    print("Scratch Output top row non-white:", np.sum(np.any(arr[0,:,:] < 255, axis=-1)))
