import json
import os
import requests

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# Target root
NEW_CLEAN_ROOT = os.path.join(WORKSPACE_DIR, "Reforma-Mattor-sortering")

def download_image(url, dest_path):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            print(f"  [DOWNLOAD SUCCESS] Saved to {dest_path}")
            return True
        else:
            print(f"  [DOWNLOAD FAILED] Status code {response.status_code} for URL: {url}")
    except Exception as e:
        print(f"  [DOWNLOAD ERROR] {e} for URL: {url}")
    return False

def main():
    missing_skus = [
        "H100143", "H100138", "H100152", "H100014", "H100072", 
        "H100080", "V10199402", "H100017", "V173401247", "V2019", 
        "V1020149000", "V1020110"
    ]
    
    brand_dict_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
    sku_map_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'sku_map.json')
    
    with open(brand_dict_path, 'r', encoding='utf-8') as f:
        brand_dict = json.load(f)
        
    with open(sku_map_path, 'r', encoding='utf-8') as f:
        sku_map = json.load(f)
        
    print("=== Downloading Missing Reference Photos ===")
    
    for sku in missing_skus:
        print(f"\nSKU: {sku}")
        
        # 1. Find the target folder in Reforma-Mattor-sortering
        target_folder = None
        for item in os.listdir(NEW_CLEAN_ROOT):
            if f"({sku})" in item:
                target_folder = os.path.join(NEW_CLEAN_ROOT, item)
                break
                
        if not target_folder:
            print(f"  Target folder for SKU {sku} not found in {NEW_CLEAN_ROOT}.")
            continue
            
        dest_path = os.path.join(target_folder, f"00_REFERENCE_{sku}.jpg")
        
        # Check if already exists (should not, but safety check)
        if os.path.exists(dest_path):
            print(f"  Reference already exists at {dest_path}")
            continue
            
        # 2. Lookup in brand_sku_dict
        image_path = None
        for slug, info in brand_dict.items():
            if info.get('sku') == sku:
                image_path = info.get('image_path')
                break
                
        # 3. Lookup in sku_map if not found
        if not image_path:
            for k, info in sku_map.items():
                if info.get('sku') == sku:
                    # Check if there is current_images
                    curr_imgs = info.get('current_images', [])
                    if curr_imgs:
                        image_path = curr_imgs[0]
                        break
                        
        if image_path:
            # Construct download URL
            if image_path.startswith("http"):
                url = image_path
            else:
                # Ensure it starts with /
                if not image_path.startswith("/"):
                    image_path = "/" + image_path
                url = f"https://www.reformasthlm.se{image_path}"
                
            print(f"  Found image path: {image_path}. Downloading from: {url}...")
            download_image(url, dest_path)
        else:
            # Try a direct guess URL based on standard structure
            guess_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}.jpg"
            print(f"  SKU not found in DB. Trying guess URL: {guess_url}...")
            if not download_image(guess_url, dest_path):
                # Try png guess
                guess_url_png = f"https://www.reformasthlm.se/bilder/artiklar/{sku}.png"
                print(f"  Trying guess URL: {guess_url_png}...")
                download_image(guess_url_png, dest_path)

if __name__ == "__main__":
    main()
