import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

print("=== SEARCHING FOR VELENNA / RG01-6 FILES ===")
for root, dirs, files in os.walk(WORKSPACE_DIR):
    for f in files:
        if "rg01-6" in f.lower() or "velenna" in f.lower():
            print(f"Workspace: {os.path.join(root, f)}")

for root, dirs, files in os.walk(ONEDRIVE_DIR):
    for f in files:
        if "rg01-6" in f.lower() or "velenna" in f.lower():
            if "Reforma-Full-Catalog-sortering" not in root:
                print(f"OneDrive: {os.path.join(root, f)}")
