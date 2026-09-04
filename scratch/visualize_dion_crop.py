import os
from PIL import Image, ImageDraw

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\armchairs\Fåtölj _Dion_ - SammetRosa\Fåtölj _Dion_ - SammetRosa-03-W-wonder.jpg"

if os.path.exists(img_path):
    with Image.open(img_path) as img:
        W, H = img.size
        # Let's draw vertical lines at x = 0.3225 * W and x = 0.699 * W
        draw = ImageDraw.Draw(img)
        draw.line([(0.3225 * W, 0), (0.3225 * W, H)], fill="red", width=10)
        draw.line([(0.699 * W, 0), (0.699 * W, H)], fill="blue", width=10)
        draw.line([(0.285 * W, 0), (0.285 * W, H)], fill="green", width=5)
        draw.line([(0.705 * W, 0), (0.705 * W, H)], fill="cyan", width=5)
        
        img.save(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\dion_original_marked.jpg")
        print("Saved marked image.")
