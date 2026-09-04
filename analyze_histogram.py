import os
from PIL import Image
import numpy as np

dir_in_out = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out"

def analyze_image_stats(filepath):
    try:
        with Image.open(filepath) as img:
            img_small = img.resize((100, 100)).convert('L') # Convert to grayscale
            arr = np.array(img_small)
            mean = np.mean(arr)
            std_dev = np.std(arr)
            # Find the ratio of very dark (< 80) and very bright (> 180) pixels
            dark_ratio = np.mean(arr < 80)
            bright_ratio = np.mean(arr > 180)
            return mean, std_dev, dark_ratio, bright_ratio
    except Exception as e:
        print(f"Error {filepath}: {e}")
    return None

sessions_to_test = {
    "Sess 1 (0001-0010, UNMAPPED)": [f"B59A000{i}.JPG" for i in range(1, 10)],
    "Dhamar-grön (0013-0020)": [f"B59A00{i}.JPG" for i in range(13, 21)],
    "Ragusa-taupe-creme (0086-0091)": [f"B59A00{i}.JPG" for i in range(86, 92)],
    "Mekele-taupe (0031-0037)": [f"B59A00{i}.JPG" for i in range(31, 38)]
}

for name, files in sessions_to_test.items():
    means, stds, darks, brights = [], [], [], []
    for f in files:
        path = os.path.join(dir_in_out, f)
        stats = analyze_image_stats(path)
        if stats is not None:
            m, s, d, b = stats
            means.append(m)
            stds.append(s)
            darks.append(d)
            brights.append(b)
            
    print(f"{name:30s} | Mean: {np.mean(means):.1f} | StdDev: {np.mean(stds):.1f} | Dark (<80): {np.mean(darks)*100:.1f}% | Bright (>180): {np.mean(brights)*100:.1f}%")
