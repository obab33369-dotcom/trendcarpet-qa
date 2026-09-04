import os
import json
import re
import requests
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

def get_sku(folder_name):
    m = re.search(r'\(([^)]+)\)', folder_name)
    if m:
        return m.group(1).strip()
    return None

def scrape_og_image(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            html = r.text
            m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            if m:
                return m.group(1)
    except Exception as e:
        print(f"    Error scraping {url}: {e}")
    return None

def download_image(url, dest_path):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(dest_path, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"    Error downloading {url}: {e}")
    return False

def main():
    # Load dictionaries
    brand_dict_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
    sku_map_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'sku_map.json')
    
    with open(brand_dict_path, 'r', encoding='utf-8') as f:
        brand_dict = json.load(f)
        
    with open(sku_map_path, 'r', encoding='utf-8') as f:
        sku_map = json.load(f)

    # 21 flagged folders
    flagged_folders = [
        "Matta Aravelle - Multi (RG01-20)",
        "Matta Arvella - RödGrön (RG01-65)",
        "Matta Aureline - BeigeBrun (RG01-8)",
        "Matta Aureline - Grön (RG01-9)",
        "Matta Aureline BeigeGrå (RG01-7)",
        "Matta Avendo - GulBeige (RG01-76)",
        "Matta Avendo - Röd (RG01-75)",
        "Matta Belden - Grön (RG01-74)",
        "Matta Belden - Röd (RG01-73)",
        "Matta Calvera - Grå (RG01-35)",
        "Matta Calvera - Röd (RG01-34)",
        "Matta Carrano - GråVit (RG01-72)",
        "Matta Carrano - Grön (RG01-71)",
        "Matta Carrano - SvartVit (RG01-70)",
        "Matta Ventaro - GrönGul (RG01-91)",
        "Matta Ventaro - Multi (RG01-87)",
        "Matta Ventaro - RosaBrun (RG01-90)",
        "Matta Ängelholm - GråBlå (RG002)",
        "Matta Ängelholm - Grön (RG00)",
        "Matta Ängelholm - Mörkbrun (RG001)",
        "Ryamatta Aranga Super Soft Fur Rosa (H100017)"
    ]
    
    print("=== STARTING LIVE REFERENCE DOWNLOADING ===")
    
    success_count = 0
    
    for folder in flagged_folders:
        sku = get_sku(folder)
        if not sku:
            continue
            
        print(f"\nFolder: {folder} (SKU: {sku})")
        
        # Determine URL
        url = None
        # 1. Look in brand_dict
        for slug, info in brand_dict.items():
            if info.get('sku') == sku:
                url = info.get('url')
                break
        # 2. Look in sku_map
        if not url:
            for k, info in sku_map.items():
                if info.get('sku') == sku:
                    url = info.get('url')
                    break
        # 3. Guess based on name
        if not url:
            # Clean up folder name
            clean_name = folder.split(' (')[0].lower()
            clean_name = clean_name.replace("å", "a").replace("ä", "a").replace("ö", "o").replace(" ", "-")
            url = f"https://www.reformasthlm.se/sv/{clean_name}"
            print(f"  Guessed URL: {url}")
            
        # Try to scrape og:image
        img_url = scrape_og_image(url)
        if not img_url and "guessed" in locals():
            # Try guessing URL with SKU
            fallback_url = f"https://www.reformasthlm.se/sv/{sku.lower()}"
            img_url = scrape_og_image(fallback_url)
            
        if not img_url:
            # Fallback to direct Shopify/standard articles image path
            img_url = f"https://www.reformasthlm.se/bilder/artiklar/{sku}.jpg"
            print(f"  Scrape failed. Trying direct link: {img_url}")
            
        # Download image to both clean and discard roots
        dest_clean = os.path.join(CLEAN_ROOT, folder, f"00_REFERENCE_{sku}.jpg")
        dest_discard = os.path.join(DISCARD_ROOT, folder, f"00_REFERENCE_{sku}.jpg")
        
        print(f"  Downloading from: {img_url}...")
        
        # Download to clean root
        if download_image(img_url, dest_clean):
            success_count += 1
            print(f"  [SUCCESS] Saved reference to clean folder: {dest_clean}")
            # Also copy to discard root if folder exists
            if os.path.exists(os.path.dirname(dest_discard)):
                shutil.copy2(dest_clean, dest_discard)
                print(f"  [SUCCESS] Copied reference to discard folder: {dest_discard}")
        else:
            # Try png fallback
            img_url_png = img_url.replace(".jpg", ".png")
            if download_image(img_url_png, dest_clean):
                success_count += 1
                print(f"  [SUCCESS] Saved PNG reference to clean folder: {dest_clean}")
                if os.path.exists(os.path.dirname(dest_discard)):
                    shutil.copy2(dest_clean, dest_discard)
            else:
                print(f"  [FAILED] Could not download reference for SKU: {sku}")
                
    print(f"\n=== DOWNLOAD COMPLETE. Successfully updated {success_count} folders. ===")

if __name__ == "__main__":
    main()
