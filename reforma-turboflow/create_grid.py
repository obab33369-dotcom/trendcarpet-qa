import os
import json
import re

FTP_UPLOAD_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v4"
STATUS_FILE = os.path.join(FTP_UPLOAD_DIR, "review_status.json")
OUTPUT_HTML = os.path.join(FTP_UPLOAD_DIR, "grid_review.html")

TEST_SKUS = [
    "100438", "100514", "102464", "102465", "102576", "108453", "1211-c", 
    "1275-white-pigmented", "1400034", "19791", "19798-grey", "2108", 
    "2251-natur-svart", "2374-walnut-svart", "2504-walnut", "45921", 
    "64015-walnut", "colinbs05", "ellecd03-black", "linesb02"
]

def main():
    print("Generating HTML grid review page...")
    
    if not os.path.exists(STATUS_FILE):
        print(f"Error: status file not found at {STATUS_FILE}")
        return
        
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = json.load(f)
        
    # Find all generated images on disk
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    sku_images = {sku: [] for sku in TEST_SKUS}
    
    # 1. Gather main images
    if os.path.exists(artiklar_dir):
        for fn in os.listdir(artiklar_dir):
            if fn.lower().endswith('.jpg') and os.path.isfile(os.path.join(artiklar_dir, fn)):
                base_sku = fn[:-4].lower()
                for sku in TEST_SKUS:
                    if base_sku == sku.lower():
                        sku_images[sku].append({
                            "type": "Main",
                            "filename": fn,
                            "path": os.path.join(artiklar_dir, fn),
                            "db_key": f"artiklar/{fn}"
                        })
                        
    # 2. Gather zoom images
    if os.path.exists(zoom_dir):
        for fn in os.listdir(zoom_dir):
            if fn.lower().endswith('.jpg') and os.path.isfile(os.path.join(zoom_dir, fn)):
                m = re.match(r"^(.+?)_\d+\.jpg$", fn, re.IGNORECASE)
                if m:
                    base_sku = m.group(1).lower()
                    for sku in TEST_SKUS:
                        if base_sku == sku.lower():
                            sku_images[sku].append({
                                "type": f"Zoom {fn.rsplit('_', 1)[-1][:-4]}",
                                "filename": fn,
                                "path": os.path.join(zoom_dir, fn),
                                "db_key": f"zoom/{fn}"
                            })

    # Generate HTML content
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html>")
    html.append("<head>")
    html.append("<title>Reforma Turboflow Image Grid Review</title>")
    html.append("<meta charset='utf-8'>")
    html.append("<style>")
    html.append("body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }")
    html.append("h1 { text-align: center; color: #ffffff; margin-bottom: 30px; font-weight: 300; }")
    html.append(".sku-section { background-color: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }")
    html.append(".sku-title { font-size: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; margin-top: 0; margin-bottom: 20px; color: #4fc3f7; }")
    html.append(".grid { display: flex; flex-wrap: wrap; gap: 20px; }")
    html.append(".card { background-color: #262626; border-radius: 6px; padding: 10px; width: 220px; box-sizing: border-box; text-align: center; border: 1px solid #333; }")
    html.append(".card img { width: 200px; height: 200px; object-fit: contain; background-color: #ffffff; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.5); display: block; margin: 0 auto 10px auto; }")
    html.append(".card-title { font-weight: bold; font-size: 14px; margin-bottom: 5px; color: #fff; }")
    html.append(".card-meta { font-size: 11px; color: #aaa; line-height: 1.4; text-align: left; background-color: #1a1a1a; padding: 6px; border-radius: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }")
    html.append(".card-meta span { color: #81c784; font-weight: bold; }")
    html.append(".no-images { color: #ff8a80; font-style: italic; }")
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.append("<h1>Reforma Turboflow: Image Grid Review</h1>")
    
    for sku in TEST_SKUS:
        html.append(f"<div class='sku-section'>")
        html.append(f"  <div class='sku-title'>SKU: {sku}</div>")
        
        images = sku_images[sku]
        if not images:
            html.append("  <div class='no-images'>No processed images found for this SKU.</div>")
        else:
            # Sort images: main first, then zooms sorted by slot number
            def get_sort_key(img):
                if img["type"] == "Main":
                    return 0
                try:
                    slot = int(re.search(r'_(\d+)\.jpg$', img["filename"], re.IGNORECASE).group(1))
                    return slot
                except Exception:
                    return 99
            images.sort(key=get_sort_key)
            
            html.append("  <div class='grid'>")
            for img in images:
                db_key = img["db_key"].lower()
                meta_entry = status_db.get(db_key, {})
                status = meta_entry.get("status", "unknown")
                category = meta_entry.get("category", "unknown")
                
                corr_meta = meta_entry.get("correction_metadata", {})
                scale = corr_meta.get("scale_applied")
                scaled_by = corr_meta.get("scaled_by", "height")
                target_h_px = corr_meta.get("target_body_h_pixels")
                target_w_px = corr_meta.get("target_body_w_pixels")
                
                # Format scale string
                scale_str = f"{scale:.4f}" if scale is not None else "N/A"
                if target_h_px is not None:
                    phys_str = f"H_px: {int(target_h_px)} | W_px: {int(target_w_px or 0)} ({scaled_by})"
                else:
                    phys_str = f"Scale: {scale_str}"
                
                # Convert absolute path to file URI for local browser access
                file_uri = "file:///" + img["path"].replace('\\', '/')
                
                html.append("    <div class='card'>")
                html.append(f"      <img src='{file_uri}' alt='{img['filename']}'>")
                html.append(f"      <div class='card-title'>{img['type']}</div>")
                html.append(f"      <div class='card-meta'>")
                html.append(f"        File: {img['filename']}<br>")
                html.append(f"        Cat: <span>{category}</span><br>")
                html.append(f"        Status: <span>{status}</span><br>")
                html.append(f"        {phys_str}")
                html.append("      </div>")
                html.append("    </div>")
            html.append("  </div>")
            
        html.append("</div>")
        
    html.append("</body>")
    html.append("</html>")
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write("\n".join(html))
        
    print(f"Successfully generated HTML grid review page at: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
