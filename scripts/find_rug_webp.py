import os

ROOT_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"

print("Searching for rug .webp files (starting with 2)...")
rug_files = []
for root, dirs, files in os.walk(ROOT_DIR):
    for f in files:
        if f.lower().endswith(".webp") and f.startswith("2"):
            rug_files.append(os.path.join(root, f))
            if len(rug_files) >= 20:
                break
    if len(rug_files) >= 20:
        break

print(f"Found {len(rug_files)} rug webp files:")
for path in rug_files:
    print(f"  {path}")
