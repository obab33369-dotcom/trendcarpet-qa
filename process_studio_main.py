import os
import shutil
import cv2
import numpy as np
import time
import json

src_root = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-new-Interior Wool carpet"
iphone_src = os.path.join(src_root, "1500px Iphone")
iphone_dst = os.path.join(src_root, "1500px Iphone-jämnt-ljus")
root_base = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

def load_img(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

def save_img(path, img, quality=98):
    ext = os.path.splitext(path)[1].lower()
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality] if ext in ['.jpg', '.jpeg', '.JPG', '.JPEG'] else []
    is_success, buffer = cv2.imencode(ext, img, encode_params)
    if is_success:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(buffer)
        return True
    return False

def process_light_normalization(src_path, dst_path):
    img = load_img(src_path)
    if img is None:
        return {"success": False, "error": "Could not read image"}
        
    h, w, c = img.shape
    
    bg_mask = (img[:,:,0] > 248) & (img[:,:,1] > 248) & (img[:,:,2] > 248)
    rug_mask = ~bg_mask
    
    coords = np.argwhere(rug_mask)
    if len(coords) == 0:
        save_img(dst_path, img, quality=98)
        return {"success": False, "error": "Empty rug mask"}
        
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(float)
    L = lab[:, :, 0]
    
    L_rug_roi = L[y_min:y_max+1, x_min:x_max+1].copy()
    mask_roi = rug_mask[y_min:y_max+1, x_min:x_max+1]
    L_rug_roi[~mask_roi] = np.nan
    
    row_means = np.nanmean(L_rug_roi, axis=1)
    y_indices = np.arange(len(row_means))
    valid = ~np.isnan(row_means)
    
    if np.sum(valid) < 10:
        save_img(dst_path, img, quality=98)
        return {"success": False, "error": "Not enough valid rows"}
        
    poly = np.polyfit(y_indices[valid], row_means[valid], deg=1)
    slope = poly[0]
    intercept = poly[1]
    L_fit = np.polyval(poly, y_indices)
    
    L_fit_2d = np.zeros((h, w), dtype=float)
    L_fit_roi = np.tile(L_fit[:, np.newaxis], (1, x_max - x_min + 1))
    L_fit_2d[y_min:y_max+1, x_min:x_max+1] = L_fit_roi
    
    # Target = center anchor (mean of the carpet)
    target_L = np.nanmean(row_means)
    
    adjustment_map = target_L - L_fit_2d
    
    weight = (255.0 - L) / (255.0 - L_fit_2d + 1e-6)
    weight = np.clip(weight, 0.0, 1.0)
    
    L_new = L.copy()
    L_new[rug_mask] = L[rug_mask] + (adjustment_map[rug_mask] * weight[rug_mask])
    L_new = np.clip(L_new, 0, 255)
    
    lab_new = lab.copy()
    lab_new[:, :, 0] = L_new
    img_out = cv2.cvtColor(lab_new.astype(np.uint8), cv2.COLOR_LAB2BGR)
    img_out[bg_mask] = img[bg_mask]
    
    save_img(dst_path, img_out, quality=98)
    
    orig_top = float(np.nanmean(row_means[:max(1, len(row_means)//10)]))
    orig_bot = float(np.nanmean(row_means[-max(1, len(row_means)//10):]))
    
    row_means_new = np.nanmean(L_new[y_min:y_max+1, x_min:x_max+1], axis=1)
    new_top = float(np.nanmean(row_means_new[:max(1, len(row_means_new)//10)]))
    new_bot = float(np.nanmean(row_means_new[-max(1, len(row_means_new)//10):]))
    
    return {
        "success": True,
        "slope": float(slope),
        "total_gradient": float(slope * len(row_means)),
        "target_L": float(target_L),
        "orig_mean_L": float(np.nanmean(row_means)),
        "new_mean_L": float(np.nanmean(row_means_new)),
        "orig_top_L": orig_top,
        "orig_bot_L": orig_bot,
        "new_top_L": new_top,
        "new_bot_L": new_bot
    }

def find_all_studio_photos():
    iphone_01_files = []
    all_studio_01_files = []
    
    for root, dirs, files in os.walk(root_base):
        if '26-new-interior' in root.lower() or 'jämnt' in root.lower():
            continue
        for f in files:
            if f.endswith(('-01.jpg', '-01.JPG', '-01.png', '-01.jpeg')) and 'interior' not in f.lower():
                full_p = os.path.join(root, f)
                if '1500' in root.lower() and 'iphone' in root.lower():
                    iphone_01_files.append(full_p)
                all_studio_01_files.append(full_p)
                
    return iphone_01_files, all_studio_01_files

def main():
    start_time = time.time()
    os.makedirs(iphone_dst, exist_ok=True)
    
    print("Searching for original studio -01 photos...")
    iphone_01_files, all_studio_01_files = find_all_studio_photos()
    print(f"Found {len(iphone_01_files)} iPhone studio photos and {len(all_studio_01_files)} total studio photos.")
    
    carpet_folders = sorted(os.listdir(iphone_src))
    manifest = []
    
    for idx, folder_name in enumerate(carpet_folders, 1):
        dst_folder_path = os.path.join(iphone_dst, folder_name)
        os.makedirs(dst_folder_path, exist_ok=True)
        
        # Match original studio -01 file
        cand = [p for p in iphone_01_files if os.path.basename(os.path.dirname(p)).lower() == folder_name.lower() or os.path.basename(p).lower().startswith(folder_name.lower())]
        if not cand:
            r_clean = folder_name.lower().replace('rund-matta-', '').replace('rundmattor-', '').replace('ryamattor-', '').replace('ullmatta-', '').replace('inomhusutomhus-matta-', '').replace('inomhusutomhusmatta-', '').replace('runda-mattor-', '')
            cand = [p for p in iphone_01_files if r_clean in os.path.basename(p).lower() or r_clean in os.path.basename(os.path.dirname(p)).lower()]
        if not cand:
            cand = [p for p in all_studio_01_files if os.path.basename(os.path.dirname(p)).lower() == folder_name.lower() or os.path.basename(p).lower().startswith(folder_name.lower())]
        if not cand:
            words = [w for w in folder_name.lower().replace('-', ' ').split() if len(w) > 3 and w not in ['matta', 'mattor', 'carpet', 'teppich', 'wool', 'cotton', 'shaggy', 'premium', 'recycled']]
            if words:
                cand = [p for p in all_studio_01_files if all(w in os.path.basename(p).lower() or w in p.lower() for w in words)]
                
        if not cand:
            print(f"[{idx:3d}/{len(carpet_folders)}] {folder_name}: NO STUDIO -01 FOUND!")
            continue
            
        src_studio_file = cand[0]
        orig_filename = os.path.basename(src_studio_file)
        base, ext = os.path.splitext(orig_filename)
        v2_filename = f"{base}_v2{ext}"
        dst_studio_file = os.path.join(dst_folder_path, v2_filename)
        
        # Save original copy into workspace cache for fast instant UI display
        cache_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors\ui_images"
        os.makedirs(cache_dir, exist_ok=True)
        
        orig_cache_name = f"{idx:03d}_orig_{folder_name}{ext}"
        v2_cache_name = f"{idx:03d}_v2_{folder_name}{ext}"
        orig_cache_path = os.path.join(cache_dir, orig_cache_name)
        v2_cache_path = os.path.join(cache_dir, v2_cache_name)
        
        shutil.copy2(src_studio_file, orig_cache_path)
        
        stats = process_light_normalization(src_studio_file, dst_studio_file)
        shutil.copy2(dst_studio_file, v2_cache_path)
        
        manifest_item = {
            "id": idx,
            "carpet_name": folder_name,
            "orig_studio_src": src_studio_file,
            "v2_studio_dst": dst_studio_file,
            "orig_filename": orig_filename,
            "v2_filename": v2_filename,
            "orig_cache_rel": f"ui_images/{orig_cache_name}",
            "v2_cache_rel": f"ui_images/{v2_cache_name}",
            "stats": stats
        }
        manifest.append(manifest_item)
        
        top_diff = stats.get('new_top_L', 0) - stats.get('orig_top_L', 0)
        bot_diff = stats.get('new_bot_L', 0) - stats.get('orig_bot_L', 0)
        print(f"[{idx:3d}/{len(carpet_folders)}] {folder_name[:40]:40} | Top: {top_diff:+.1f} | Bot: {bot_diff:+.1f} | Center: {stats.get('target_L', 0):.1f}")
        
    json_path = os.path.join(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors", "carpets_studio_metadata.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    onedrive_json = os.path.join(src_root, "carpets_studio_metadata.json")
    with open(onedrive_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    print(f"\nCOMPLETED: Processed {len(manifest)} studio images in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
