import os

ROOT_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch"

print("Searching for .webp files in scratch directory...")
webp_files = []
for root, dirs, files in os.walk(ROOT_DIR):
    for f in files:
        if f.lower().endswith(".webp"):
            webp_files.append(os.path.join(root, f))
            if len(webp_files) >= 30:
                break
    if len(webp_files) >= 30:
        break

print(f"Found {len(webp_files)} webp files (showing up to first 30):")
for path in webp_files:
    print(f"  {path}")
