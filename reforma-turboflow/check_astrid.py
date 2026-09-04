import os
from PIL import Image
import numpy as np

folder = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\Refoma chair\1 Stol _Astrid_ - Vitpigmenterad"
files = os.listdir(folder)
print("Files in Astrid folder:")
for f in files:
    fp = os.path.join(folder, f)
    if os.path.isfile(fp) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
        with Image.open(fp) as img:
            arr = np.array(img.convert("RGB"))
            # Check corners
            patches = [
                arr[10:20, 10:20],
                arr[10:20, -20:-10],
                arr[-20:-10, 10:20],
                arr[-20:-10, -20:-10]
            ]
            means = [np.mean(pat, axis=(0,1)) for pat in patches]
            means.sort(key=lambda c: np.sum(c))
            bg_color = np.mean(means[1:], axis=0)
            bg_mean = np.mean(bg_color)
            print(f"  {f}: size={img.size}, Corner Means={ [list(m.astype(int)) for m in means] }, bg_mean={bg_mean:.1f}")
