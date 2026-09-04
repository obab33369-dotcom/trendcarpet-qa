import os
import shutil
import json
import re

SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v4"
DST_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\review_test_20_only"

TEST_SKUS = [
    "100438", "100514", "102464", "102465", "102576", "108453", "1211-c", 
    "1275-white-pigmented", "1400034", "19791", "19798-grey", "2108", 
    "2251-natur-svart", "2374-walnut-svart", "2504-walnut", "45921", 
    "64015-walnut", "colinbs05", "ellecd03-black", "linesb02"
]

def main():
    print(f"Creating clean review folder for 20 SKUs at: {DST_DIR}")
    
    # Create target directories
    dst_artiklar = os.path.join(DST_DIR, "artiklar")
    dst_zoom = os.path.join(dst_artiklar, "zoom")
    os.makedirs(dst_zoom, exist_ok=True)
    
    src_artiklar = os.path.join(SRC_DIR, "artiklar")
    src_zoom = os.path.join(src_artiklar, "zoom")
    
    # Load status file
    src_status = os.path.join(SRC_DIR, "review_status.json")
    status_db = {}
    if os.path.exists(src_status):
        with open(src_status, 'r', encoding='utf-8') as f:
            status_db = json.load(f)
            
    copied_status = {}
    
    # 1. Copy main images
    if os.path.exists(src_artiklar):
        for fn in os.listdir(src_artiklar):
            if fn.lower().endswith('.jpg') and os.path.isfile(os.path.join(src_artiklar, fn)):
                base_sku = fn[:-4].lower()
                for sku in TEST_SKUS:
                    if base_sku == sku.lower():
                        src_path = os.path.join(src_artiklar, fn)
                        dst_path = os.path.join(dst_artiklar, fn)
                        shutil.copy2(src_path, dst_path)
                        print(f"Copied Main: {fn}")
                        db_key = f"artiklar/{fn}"
                        if db_key.lower() in [k.lower() for k in status_db.keys()]:
                            # find original case key
                            orig_key = [k for k in status_db.keys() if k.lower() == db_key.lower()][0]
                            copied_status[db_key] = status_db[orig_key]
                            
    # 2. Copy zoom images
    if os.path.exists(src_zoom):
        for fn in os.listdir(src_zoom):
            if fn.lower().endswith('.jpg') and os.path.isfile(os.path.join(src_zoom, fn)):
                m = re.match(r"^(.+?)_\d+\.jpg$", fn, re.IGNORECASE)
                if m:
                    base_sku = m.group(1).lower()
                    for sku in TEST_SKUS:
                        if base_sku == sku.lower():
                            src_path = os.path.join(src_zoom, fn)
                            dst_path = os.path.join(dst_zoom, fn)
                            shutil.copy2(src_path, dst_path)
                            print(f"Copied Zoom: {fn}")
                            db_key = f"zoom/{fn}"
                            if db_key.lower() in [k.lower() for k in status_db.keys()]:
                                orig_key = [k for k in status_db.keys() if k.lower() == db_key.lower()][0]
                                copied_status[db_key] = status_db[orig_key]

    # Save filtered status db
    with open(os.path.join(DST_DIR, "review_status.json"), 'w', encoding='utf-8') as f:
        json.dump(copied_status, f, indent=4, ensure_ascii=False)
        
    # Generate HTML grid review page with relative paths so it opens anywhere
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html>")
    html.append("<head>")
    html.append("<title>Reforma Turboflow 20 SKU Review Grid</title>")
    html.append("<meta charset='utf-8'>")
    html.append("<style>")
    html.append("body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }")
    html.append("h1 { text-align: center; color: #ffffff; margin-bottom: 10px; font-weight: 300; }")
    html.append(".subtitle { text-align: center; color: #aaa; margin-bottom: 30px; font-size: 14px; }")
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
    html.append("<h1>Reforma Turboflow: 20 SKU Review Grid</h1>")
    html.append("<div class='subtitle'>Rent och städat galleri med endast de 20 testmöblerna. Öppna bilderna i mappen review_test_20_only.</div>")
    
    for sku in TEST_SKUS:
        html.append(f"<div class='sku-section'>")
        html.append(f"  <div class='sku-title'>SKU: {sku}</div>")
        
        # Find copied images
        sku_imgs = []
        # Main
        main_fn = f"{sku}.jpg"
        if os.path.exists(os.path.join(dst_artiklar, main_fn)):
            sku_imgs.append({
                "type": "Main",
                "filename": main_fn,
                "rel_path": f"artiklar/{main_fn}",
                "db_key": f"artiklar/{main_fn}"
            })
        elif os.path.exists(os.path.join(dst_artiklar, main_fn.lower())):
            sku_imgs.append({
                "type": "Main",
                "filename": main_fn.lower(),
                "rel_path": f"artiklar/{main_fn.lower()}",
                "db_key": f"artiklar/{main_fn.lower()}"
            })
            
        # Zooms
        if os.path.exists(dst_zoom):
            for fn in os.listdir(dst_zoom):
                m = re.match(r"^(.+?)_(\d+)\.jpg$", fn, re.IGNORECASE)
                if m and m.group(1).lower() == sku.lower():
                    sku_imgs.append({
                        "type": f"Zoom {m.group(2)}",
                        "filename": fn,
                        "rel_path": f"artiklar/zoom/{fn}",
                        "db_key": f"zoom/{fn}"
                    })
                    
        if not sku_imgs:
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
            sku_imgs.sort(key=get_sort_key)
            
            html.append("  <div class='grid'>")
            for img in sku_imgs:
                db_key = img["db_key"].lower()
                meta_entry = copied_status.get(db_key, {})
                status = meta_entry.get("status", "unknown")
                category = meta_entry.get("category", "unknown")
                
                corr_meta = meta_entry.get("correction_metadata", {})
                scale = corr_meta.get("scale_applied")
                scaled_by = corr_meta.get("scaled_by", "height")
                target_h_px = corr_meta.get("target_body_h_pixels")
                target_w_px = corr_meta.get("target_body_w_pixels")
                
                scale_str = f"{scale:.4f}" if scale is not None else "N/A"
                if target_h_px is not None:
                    phys_str = f"H_px: {int(target_h_px)} | W_px: {int(target_w_px or 0)} ({scaled_by})"
                else:
                    phys_str = f"Scale: {scale_str}"
                
                html.append("    <div class='card'>")
                # Use relative path so it loads perfectly in any local browser
                html.append(f"      <img src='{img['rel_path']}' alt='{img['filename']}'>")
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
    
    output_html = os.path.join(DST_DIR, "grid_review.html")
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write("\n".join(html))
        
    print(f"Successfully generated clean review grid at: {output_html}")

if __name__ == "__main__":
    main()
