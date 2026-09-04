import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

target_folders = [
    "Barstol Forshaga - Silver (KS-01-M-silver)",
    "Barstol Forshaga - SilverNatur (KS-01-W-wood)",
    "Matbord rsj Runt 105cm - Natur (91517)",
    "Matgrupp Hornstull Forma 1 Bord & 4 Stolar (matgrupp28)",
    "Matgrupp Kungsholmen Hornstull - 1 Bord & 4 Stolar (matgrupp7)",
    "Matgrupp Kungsholmen Montmartre - 1 Bord & 4 Stolar (matgrupp26)",
    "Matgrupp Marbelous Elsa - 1 Bord 120 & 6 Stolar (matgrupp17)",
    "Matgrupp Nordisk Elsa - 1 Bord & 4 Stolar (matgrupp42)",
    "Matgrupp Runt Kungsholmen - 1 Bord & 4 Stolar (matgrupp23)",
    "Matgrupp Vega Elsa - 1 Bord & 6 Stolar (matgrupp51)",
    "Sngbord Haninge - Vit (96292)",
    "Sngbord Sand - Ek (08-natural)",
    "Sngbord Sapporo - NaturMetall - Reforma Sthlm (9375%20Oak)",
    "Sngbord Twine - ValntSvart (21703-walnut)",
    "Tv-bnk Lvhamn L- Natur (2502-natur)",
    "Tv-bnk Myshult 160x55cm - Natur (2372-1-natur)",
    "Vgghylla Joliet - Svart (89382)"
]

def main():
    print("=== Discarded Filenames Check ===")
    for folder in target_folders:
        path = os.path.join(DISCARD_ROOT, folder)
        if not os.path.exists(path):
            print(f"Folder does not exist: {folder}")
            continue
            
        files = [f for f in os.listdir(path) if not f.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(path, f))]
        print(f"\nFolder: {folder} ({len(files)} files)")
        for f in files[:3]: # print first 3
            m = re.match(r"^(\d+)", f)
            prefix = m.group(1) if m else "No prefix"
            print(f"  * {f} -> Prefix: {prefix}")
        if len(files) > 3:
            print(f"  ... and {len(files) - 3} more.")

if __name__ == "__main__":
    main()
