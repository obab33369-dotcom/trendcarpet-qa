import os
import shutil
import cv2
import numpy as np
import time
import json

src_root = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-new-Interior Wool carpet"
iphone_src = os.path.join(src_root, "1500px Iphone")
iphone_dst = os.path.join(src_root, "1500px Iphone-jämnt-ljus")

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
        shutil.copy2(src_path, dst_path)
        return {"success": False, "error": "Could not read image"}
        
    h, w, c = img.shape
    
    bg_mask = (img[:,:,0] > 248) & (img[:,:,1] > 248) & (img[:,:,2] > 248)
    rug_mask = ~bg_mask
    
    coords = np.argwhere(rug_mask)
    if len(coords) == 0:
        shutil.copy2(src_path, dst_path)
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
        shutil.copy2(src_path, dst_path)
        return {"success": False, "error": "Not enough valid rows"}
        
    poly = np.polyfit(y_indices[valid], row_means[valid], deg=1)
    slope = poly[0]
    intercept = poly[1]
    L_fit = np.polyval(poly, y_indices)
    
    L_fit_2d = np.zeros((h, w), dtype=float)
    L_fit_roi = np.tile(L_fit[:, np.newaxis], (1, x_max - x_min + 1))
    L_fit_2d[y_min:y_max+1, x_min:x_max+1] = L_fit_roi
    
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

def main():
    start_time = time.time()
    print("=" * 60)
    print("Processing 26-new-Interior Wool carpet (1500px Iphone)")
    print(f"Source:      {iphone_src}")
    print(f"Destination: {iphone_dst}")
    print("=" * 60)
    
    os.makedirs(iphone_dst, exist_ok=True)
    carpet_folders = sorted(os.listdir(iphone_src))
    print(f"Found {len(carpet_folders)} carpet folders.")
    
    manifest = []
    
    for idx, folder_name in enumerate(carpet_folders, 1):
        src_folder_path = os.path.join(iphone_src, folder_name)
        if not os.path.isdir(src_folder_path):
            continue
            
        dst_folder_path = os.path.join(iphone_dst, folder_name)
        os.makedirs(dst_folder_path, exist_ok=True)
        
        files = sorted(os.listdir(src_folder_path))
        if len(files) < 1:
            print(f"[{idx:3d}/{len(carpet_folders)}] {folder_name}: No files found!")
            continue
            
        file1 = files[0]
        base1, ext1 = os.path.splitext(file1)
        file1_v2 = f"{base1}_v2{ext1}"
        src_file1_path = os.path.join(src_folder_path, file1)
        dst_file1_path = os.path.join(dst_folder_path, file1_v2)
        
        stats = process_light_normalization(src_file1_path, dst_file1_path)
        
        file2_info = None
        if len(files) >= 2:
            file2 = files[1]
            base2, ext2 = os.path.splitext(file2)
            file2_v2 = f"{base2}_v2{ext2}"
            src_file2_path = os.path.join(src_folder_path, file2)
            dst_file2_path = os.path.join(dst_folder_path, file2_v2)
            shutil.copy2(src_file2_path, dst_file2_path)
            file2_info = {
                "orig_filename": file2,
                "v2_filename": file2_v2,
                "orig_rel_path": f"1500px Iphone/{folder_name}/{file2}",
                "v2_rel_path": f"1500px Iphone-jämnt-ljus/{folder_name}/{file2_v2}"
            }
            
        manifest_item = {
            "id": idx,
            "carpet_name": folder_name,
            "folder_name": folder_name,
            "image1": {
                "orig_filename": file1,
                "v2_filename": file1_v2,
                "orig_rel_path": f"1500px Iphone/{folder_name}/{file1}",
                "v2_rel_path": f"1500px Iphone-jämnt-ljus/{folder_name}/{file1_v2}",
                "orig_abs_path": src_file1_path,
                "v2_abs_path": dst_file1_path,
                "stats": stats
            },
            "image2": file2_info
        }
        manifest.append(manifest_item)
        
        top_diff = stats.get('new_top_L', 0) - stats.get('orig_top_L', 0)
        bot_diff = stats.get('new_bot_L', 0) - stats.get('orig_bot_L', 0)
        print(f"[{idx:3d}/{len(carpet_folders)}] {folder_name[:42]:42} | Top: {top_diff:+.1f} | Bot: {bot_diff:+.1f} | Center: {stats.get('target_L', 0):.1f}")
        
    manifest_root_path = os.path.join(src_root, "carpets_metadata.json")
    with open(manifest_root_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    manifest_local_path = os.path.join(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors", "carpets_metadata.json")
    with open(manifest_local_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"SUCCESS: Processed {len(manifest)} carpets in {elapsed:.2f}s")
    print(f"Metadata saved to: {manifest_root_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
