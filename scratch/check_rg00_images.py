import os
from PIL import Image

def compute_mae(img1_path, img2_path):
    try:
        img1 = Image.open(img1_path).convert('L').resize((256, 256))
        img2 = Image.open(img2_path).convert('L').resize((256, 256))
        pixels1 = list(img1.getdata())
        pixels2 = list(img2.getdata())
        return sum(abs(p1 - p2) for p1, p2 in zip(pixels1, pixels2)) / (256 * 256)
    except Exception as e:
        print(f"Error comparing {img1_path} and {img2_path}: {e}")
        return None

web_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\audit_images\web_RG00.jpg"
local_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\audit_images\local_RG00.jpg"

paths = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Matta 'Ängelholm' - Grön (RG00)\artiklar\RG00.jpg",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-Mattor-sortering-NEW\Matta Ängelholm - Grön (RG00)\00_REFERENCE_RG00.jpg",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering\Matta Ängelholm - Grön (RG00)\00_REFERENCE_RG00.jpg"
]

print("--- RG00 IMAGE CHECK ---")
for p in paths:
    if os.path.exists(p):
        mae_web = compute_mae(p, web_path)
        mae_local = compute_mae(p, local_path)
        print(f"File: {p}")
        if mae_web is not None:
            print(f"  MAE to Web (Green): {mae_web:.2f}")
            print(f"  MAE to Local (Blue): {mae_local:.2f}")
    else:
        print(f"Not found: {p}")
