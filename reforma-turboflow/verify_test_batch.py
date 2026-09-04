import os

output_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\missed-products-upload\zara_style_batch20"
artiklar_dir = os.path.join(output_dir, "artiklar")
liten_dir = os.path.join(artiklar_dir, "liten")
zoom_dir = os.path.join(artiklar_dir, "zoom")

print("Checking test batch output directories:")
print("artiklar_dir exists:", os.path.exists(artiklar_dir))
print("liten_dir exists:", os.path.exists(liten_dir))
print("zoom_dir exists:", os.path.exists(zoom_dir))

if os.path.exists(artiklar_dir):
    files = [f for f in os.listdir(artiklar_dir) if os.path.isfile(os.path.join(artiklar_dir, f))]
    print(f"\nFiles in artiklar/ ({len(files)}):")
    print(files[:10])

if os.path.exists(liten_dir):
    files = [f for f in os.listdir(liten_dir) if os.path.isfile(os.path.join(liten_dir, f))]
    print(f"\nFiles in artiklar/liten/ ({len(files)}):")
    print(files[:10])

if os.path.exists(zoom_dir):
    files = [f for f in os.listdir(zoom_dir) if os.path.isfile(os.path.join(zoom_dir, f))]
    print(f"\nFiles in artiklar/zoom/ ({len(files)}):")
    print(files[:20])
