import os
import zipfile
import json
import shutil
from PIL import Image

ZIP_PATH = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-08-27-Print-h-r-g-pt1-20260831T104302Z-1-001.zip"
TARGET_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-08-27-Print-h-r-g-pt1-x"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors"
METADATA_PATH = os.path.join(WORKSPACE_DIR, "pt1_gallery_metadata.json")

def extract_archive():
    print(f"Opening zip: {ZIP_PATH}")
    if not os.path.exists(ZIP_PATH):
        raise FileNotFoundError(f"Zip file not found: {ZIP_PATH}")

    os.makedirs(TARGET_DIR, exist_ok=True)
    
    extracted_count = 0
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
                
            raw_filename = member.filename
            
            # Strip the leading top-level directory e.g. "26-08-27-Print-h-r-g-pt1/"
            parts = raw_filename.split('/')
            if len(parts) > 1 and parts[0].startswith("26-08-27-Print"):
                rel_path = os.path.join(*parts[1:])
            else:
                rel_path = os.path.join(*parts)
                
            out_file_path = os.path.join(TARGET_DIR, rel_path)
            os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
            
            with zf.open(member) as source, open(out_file_path, "wb") as target:
                shutil.copyfileobj(source, target)
                
            extracted_count += 1
            
    print(f"Successfully extracted {extracted_count} files to: {TARGET_DIR}")

def scan_and_build_metadata():
    print(f"Scanning target directory: {TARGET_DIR}")
    catalog = {
        "batch_name": "26-08-27-Print-h-r-g-pt1-x",
        "root_dir": TARGET_DIR,
        "categories": ["1500px", "1500px iphone", "Original"],
        "rugs": {},
        "all_images": []
    }
    
    for root, dirs, files in os.walk(TARGET_DIR):
        for f in sorted(files):
            if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
                
            full_path = os.path.join(root, f)
            rel_to_target = os.path.relpath(full_path, TARGET_DIR).replace('\\', '/')
            parts = rel_to_target.split('/')
            
            if len(parts) >= 3:
                category = parts[0]
                rug_name = parts[1]
                filename = parts[2]
            else:
                category = "Other"
                rug_name = "Unknown"
                filename = f
                
            is_interior = "-Interior-" in filename or "interior" in filename.lower()
            img_type = "interior" if is_interior else "studio"
            
            file_size = os.path.getsize(full_path)
            
            width, height = 0, 0
            try:
                with Image.open(full_path) as img:
                    width, height = img.size
            except Exception:
                pass
                
            item = {
                "id": f"{rug_name}_{category}_{filename}",
                "filename": filename,
                "rug_name": rug_name,
                "category": category,
                "rel_path": rel_to_target,
                "type": img_type,
                "file_size": file_size,
                "file_size_formatted": f"{file_size / (1024*1024):.2f} MB" if file_size > 1024*1024 else f"{file_size / 1024:.1f} KB",
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 2) if height > 0 else 1.0
            }
            
            if rug_name not in catalog["rugs"]:
                catalog["rugs"][rug_name] = {
                    "name": rug_name,
                    "categories": {},
                    "total_images": 0
                }
                
            if category not in catalog["rugs"][rug_name]["categories"]:
                catalog["rugs"][rug_name]["categories"][category] = []
                
            catalog["rugs"][rug_name]["categories"][category].append(item)
            catalog["rugs"][rug_name]["total_images"] += 1
            catalog["all_images"].append(item)
            
    for rug_name, rug_data in catalog["rugs"].items():
        for cat, items in rug_data["categories"].items():
            items.sort(key=lambda x: x["filename"])
            
    print(f"Total rug models found: {len(catalog['rugs'])}")
    print(f"Total images indexed: {len(catalog['all_images'])}")
    
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        
    print(f"Saved catalog metadata to: {METADATA_PATH}")

if __name__ == "__main__":
    extract_archive()
    scan_and_build_metadata()
