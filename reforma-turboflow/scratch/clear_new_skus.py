import os
import json
import shutil

# 1. Paths to clear
onedrive_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ftp_dir = os.path.join(onedrive_dir, "26-06-18-FTP")
artiklar_dir = os.path.join(ftp_dir, "artiklar")
inte_artiklar_dir = os.path.join(ftp_dir, "Inte-dessa-Uppdaterade-på-sajt-undersök-FTP", "artiklar")

print("==================================================")
print("1. CLEARING FILES IN FTP DIRECTORIES")
print("==================================================")

def empty_dir(dir_path):
    if not os.path.exists(dir_path):
        print(f"Dir {dir_path} does not exist. Skipping.")
        return
    deleted_count = 0
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        try:
            if os.path.isfile(item_path):
                os.remove(item_path)
                deleted_count += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                deleted_count += 1
        except Exception as e:
            print(f"  Error deleting {item}: {e}")
    print(f"Cleaned {deleted_count} items from {dir_path}")

empty_dir(artiklar_dir)
empty_dir(inte_artiklar_dir)

# 2. Clear caches for new SKUs
print("\n==================================================")
print("2. CLEARING CACHE & BBOX DB FOR NEW SKUS")
print("==================================================")

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
cache_path = os.path.join(project_dir, "scratch", "classification_cache.json")
bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

new_skus = ["67099", "67100", "1400034", "H000017689", "2300103"]

def clear_cache_for_skus(file_path, skus):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Skipping.")
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        initial_len = len(data)
        keys_to_delete = []
        for key in data.keys():
            for sku in skus:
                if sku.lower() in key.lower():
                    keys_to_delete.append(key)
                    break
        
        for key in keys_to_delete:
            del data[key]
            
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Cleaned {len(keys_to_delete)} entries from {os.path.basename(file_path)}. (Size reduced from {initial_len} to {len(data)})")
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")

clear_cache_for_skus(cache_path, new_skus)
clear_cache_for_skus(bbox_path, new_skus)

print("Caches cleared successfully.")
