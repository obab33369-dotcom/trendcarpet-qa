import os
import re

onedrive_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
topaz_dir = os.path.join(onedrive_dir, "TEST TOPAZ")
fallback_dir = os.path.join(onedrive_dir, "reforma_original_images_by_product")

print("Checking topaz files for 'dion' or '1200180':")
if os.path.exists(topaz_dir):
    for f in os.listdir(topaz_dir):
        if "dion" in f.lower() or "1200180" in f.lower():
            print(" - Topaz:", f)

print("Checking fallback folders for 'dion' or '1200180':")
if os.path.exists(fallback_dir):
    for d in os.listdir(fallback_dir):
        if "dion" in d.lower() or "1200180" in d.lower():
            print(" - Fallback dir:", d)
            art_dir = os.path.join(fallback_dir, d, "artiklar")
            if os.path.exists(art_dir):
                for f in os.listdir(art_dir):
                    print("   -", f)

print("Checking topaz files for 'oviken' or '37281105':")
if os.path.exists(topaz_dir):
    for f in os.listdir(topaz_dir):
        if "oviken" in f.lower() or "37281105" in f.lower():
            print(" - Topaz:", f)

print("Checking fallback folders for 'oviken' or '37281105':")
if os.path.exists(fallback_dir):
    for d in os.listdir(fallback_dir):
        if "oviken" in d.lower() or "37281105" in d.lower():
            print(" - Fallback dir:", d)
            art_dir = os.path.join(fallback_dir, d, "artiklar")
            if os.path.exists(art_dir):
                for f in os.listdir(art_dir):
                    print("   -", f)
