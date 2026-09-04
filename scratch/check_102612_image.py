import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    dirs = [
        os.path.join(WORKSPACE_DIR, "reforma-original-images"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar")
    ]
    
    sku = "102612"
    for d in dirs:
        print(f"Checking {d} for SKU {sku}...")
        found = False
        if os.path.exists(d):
            for f in os.listdir(d):
                if sku in f:
                    print(f"  Found: {f}")
                    found = True
        if not found:
            print("  No files found.")

if __name__ == "__main__":
    main()
