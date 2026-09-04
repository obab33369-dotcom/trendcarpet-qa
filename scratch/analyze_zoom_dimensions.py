import os
from PIL import Image

dir_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_studio_only\artiklar\zoom"

if not os.path.exists(dir_path):
    print(f"Directory not found: {dir_path}")
    sys.exit(1)

files = [f for f in os.listdir(dir_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
print(f"Total zoom images to analyze: {len(files)}")

square_count = 0
non_square_count = 0
non_square_examples = []

for f in files:
    p = os.path.join(dir_path, f)
    try:
        with Image.open(p) as img:
            w, h = img.size
            if w == h:
                square_count += 1
            else:
                non_square_count += 1
                if len(non_square_examples) < 15:
                    non_square_examples.append((f, f"{w}x{h}"))
    except Exception as e:
        print(f"Error reading {f}: {e}")

print(f"\nResults:")
print(f"  Square images (e.g. 2000x2000): {square_count}")
print(f"  Non-square images:               {non_square_count}")
print(f"\nExamples of non-square images:")
for f, dim in non_square_examples:
    print(f"  - {f} ({dim})")
