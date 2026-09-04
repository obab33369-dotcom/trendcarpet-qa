import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def search_files(base_dir, patterns):
    results = []
    if not os.path.exists(base_dir):
        return results
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            for p in patterns:
                if p.lower() in f.lower():
                    results.append(os.path.join(root, f))
    return results

patterns = ["0108", "1397", "MLM-502580"]

print("=== Searching in Workspace ===")
for r in search_files(WORKSPACE_DIR, patterns):
    print(r)

print("\n=== Searching in OneDrive ===")
for r in search_files(ONEDRIVE_DIR, patterns)[:20]:
    print(r)
