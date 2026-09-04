import json
import os

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    missing_skus = [
        "RG01-20", "RG01-65", "RG01-8", "RG01-9", "RG01-7", "RG01-76",
        "RG01-75", "RG01-74", "RG01-73", "RG01-35", "RG01-34", "RG01-72",
        "RG01-71", "RG01-70", "RG01-91", "RG01-87", "RG01-90", "RG002",
        "RG00", "RG001", "H100017"
    ]
    
    brand_dict_path = os.path.join(PROJECT_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
    with open(brand_dict_path, 'r', encoding='utf-8') as f:
        brand_dict = json.load(f)
        
    print("=== Checking URLs in brand_sku_dict.json ===")
    found_count = 0
    for sku in missing_skus:
        # Search by SKU
        url = None
        for slug, info in brand_dict.items():
            if info.get('sku') == sku:
                url = info.get('url')
                break
        if url:
            print(f"  SKU: {sku} -> {url}")
            found_count += 1
        else:
            print(f"  SKU: {sku} -> NOT FOUND")
            
    print(f"\nFound URLs for {found_count} out of {len(missing_skus)} SKUs.")

if __name__ == "__main__":
    main()
