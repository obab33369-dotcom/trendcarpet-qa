import os

dir_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Pall 'Marcos' - Vit (1400042)\artiklar"

# Slot 1
p1 = os.path.join(dir_path, "1400042.jpg")
if os.path.exists(p1):
    sig1 = f"{os.path.getsize(p1)}_{int(os.path.getmtime(p1))}"
    print(f"Slot 1 (1400042.jpg): size={os.path.getsize(p1)}, mtime={int(os.path.getmtime(p1))}, sig={sig1}")

# Zoom slots
zoom_dir = os.path.join(dir_path, "zoom")
if os.path.exists(zoom_dir):
    for f in sorted(os.listdir(zoom_dir)):
        p = os.path.join(zoom_dir, f)
        if os.path.isfile(p):
            sig = f"{os.path.getsize(p)}_{int(os.path.getmtime(p))}"
            print(f"{f}: size={os.path.getsize(p)}, mtime={int(os.path.getmtime(p))}, sig={sig}")
