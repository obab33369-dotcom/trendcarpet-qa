import os
from PIL import Image
from PIL.ExifTags import TAGS

root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-Full-Catalog-sortering"

# Find a generated render file (we avoid 00_REFERENCE files)
found_files = []
for root, dirs, files in os.walk(root_dir):
    for f in files:
        if f.lower().endswith(('.png', '.webp')) and not "reference" in f.lower() and not f.startswith("00_"):
            found_files.append(os.path.join(root, f))
            if len(found_files) >= 5:
                break
    if len(found_files) >= 5:
        break

if not found_files:
    print("No generated render files found in the directory.")
else:
    for path in found_files:
        print(f"\n=========================================\nInspecting file: {path}")
        try:
            img = Image.open(path)
            print("Format:", img.format)
            print("Mode:", img.mode)
            print("Size:", img.size)
            
            print("\n--- Image Info (img.info) ---")
            for k, v in img.info.items():
                v_str = str(v)
                if len(v_str) > 200:
                    v_str = v_str[:200] + "... [TRUNCATED]"
                print(f"{k}: {v_str}")
                
            exif = img.getexif()
            if exif:
                print("\n--- EXIF tags ---")
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    print(f"{tag}: {value}")
            else:
                print("\nNo EXIF tags found.")
                
        except Exception as e:
            print(f"Error inspecting file: {e}")
