import os
import json
import shutil
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b"

# Find the file path
src_file = None
for root, dirs, files in os.walk(ORIG_DIR):
    if "97828" in root.lower():
        for f in files:
            if "97828_5" in f:
                src_file = os.path.join(root, f)
                break
        if src_file:
            break

if src_file and os.path.exists(src_file):
    print(f"Found original file: {src_file}")
    # Copy original to artifacts
    dest_orig = os.path.join(ARTIFACTS_DIR, "orig_97828_5.jpg")
    shutil.copy(src_file, dest_orig)
    print(f"Copied original to {dest_orig}")
    
    # Load SAM3 bbox
    with open("scratch/bbox_coordinates_db.json", "r") as f:
        bbox_db = json.load(f)
    bbox = bbox_db.get("97828_5")
    print(f"SAM3 bbox: {bbox}")
    
    with Image.open(src_file) as img:
        w, h = img.size
        # BBox coordinates are relative to 2000px scaled image
        # Let's scale the bbox coordinates back to the original size (960x690)
        scale_w = w / 2000.0
        scale_h = h / 2000.0 # Wait, the scale factor in the pipeline was 2000.0 / max(w, h)
        scale_factor = 2000.0 / max(w, h) # which is 2000 / 960 = 2.0833
        
        # BBox relative to original size:
        x_min = int(bbox[0] / scale_factor)
        y_min = int(bbox[1] / scale_factor)
        x_max = int(bbox[2] / scale_factor)
        y_max = int(bbox[3] / scale_factor)
        print(f"Original coordinates for crop: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
        
        # Crop and save to artifacts
        cropped = img.crop((x_min, y_min, x_max, y_max))
        dest_crop = os.path.join(ARTIFACTS_DIR, "crop_97828_5.jpg")
        cropped.save(dest_crop)
        print(f"Saved cropped image to {dest_crop}")
else:
    print("97828_5.jpg not found in ORIG_DIR")
