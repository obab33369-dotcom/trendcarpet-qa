import os
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"

def main():
    folders = [
        "Matta Velenna 160x230 cm - Bl (RG016)",
        "Matta Velenna 160x230 cm - RdBeige (RG018)"
    ]
    for f in folders:
        # Resolve folder name by scanning Clean Root if names have slight differences
        matched = None
        for item in os.listdir(CLEAN_ROOT):
            if f.split(' (')[0] in item:
                matched = item
                break
        if not matched:
            print(f"Not found: {f}")
            continue
            
        src_dir = os.path.join(CLEAN_ROOT, matched)
        for item in os.listdir(src_dir):
            if item.startswith("00_REFERENCE_"):
                shutil.copy2(os.path.join(src_dir, item), os.path.join(ARTIFACTS_DIR, item))
                print(f"Copied {item} to artifacts.")

if __name__ == "__main__":
    main()
