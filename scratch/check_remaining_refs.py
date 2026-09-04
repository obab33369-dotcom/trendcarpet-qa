import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# Target root
NEW_CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")

def main():
    missing_skus = [
        "H100143", "H100138", "H100152", "H100014", "H100072", 
        "H100080", "V10199402", "H100017", "V173401247", "V2019", 
        "V1020149000", "V1020110"
    ]
    
    print("=== Checking for missing reference files ===")
    
    # 1. Check if they exist in any folder in OneDrive
    for sku in missing_skus:
        print(f"\nSKU: {sku}")
        found_paths = []
        for root, dirs, files in os.walk(ONEDRIVE_DIR):
            for f in files:
                if sku in f and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    found_paths.append(os.path.join(root, f))
        
        # Also check workspace
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            if "node_modules" in root or ".git" in root or "__pycache__" in root:
                continue
            for f in files:
                if sku in f and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    found_paths.append(os.path.join(root, f))
                    
        if found_paths:
            print(f"  Found {len(found_paths)} potential files:")
            for p in found_paths[:5]:
                print(f"    - {p}")
        else:
            print("  No files found anywhere on system.")

if __name__ == "__main__":
    main()
