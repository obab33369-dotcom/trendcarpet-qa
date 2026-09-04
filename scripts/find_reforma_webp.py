import os

ROOT_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"

print("Searching for .webp files in reforma-turboflow...")
webp_files = []
for root, dirs, files in os.walk(ROOT_DIR):
    for f in files:
        if f.lower().endswith(".webp"):
            webp_files.append(os.path.join(root, f))
            if len(webp_files) >= 50:
                break
    if len(webp_files) >= 50:
        break

print(f"Found {len(webp_files)} webp files:")
for path in webp_files[:50]:
    print(f"  {path}")
