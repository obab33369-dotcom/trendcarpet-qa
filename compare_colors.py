import os
from PIL import Image
import numpy as np

dir_in_out = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out"

def get_average_color(filepath):
    try:
        with Image.open(filepath) as img:
            img_small = img.resize((50, 50))
            arr = np.array(img_small)
            if len(arr.shape) == 3:
                return np.mean(arr, axis=(0, 1))
    except Exception as e:
        print(f"Error {filepath}: {e}")
    return None

# Let's check the average colors of some files
sessions_to_test = {
    "Sess 1 (0001-0010, UNMAPPED)": [f"B59A000{i}.JPG" for i in range(1, 10)],
    "Dhamar-grön (0013-0020)": [f"B59A00{i}.JPG" for i in range(13, 21)],
    "Mekele-taupe (0031-0037)": [f"B59A00{i}.JPG" for i in range(31, 38)],
    "Devon-brun (0049-0055)": [f"B59A00{i}.JPG" for i in range(49, 56)],
    "Tracino-taupe (0067-0071)": [f"B59A00{i}.JPG" for i in range(67, 72)],
    "Ragusa-taupe-creme (0086-0091)": [f"B59A00{i}.JPG" for i in range(86, 92)],
    "Cordoba-taupe (0100-0104)": [f"B59A0{i}.JPG" for i in range(100, 105)],
    "Mekele-brun (0117-0122)": [f"B59A0{i}.JPG" for i in range(117, 123)],
    "Djerba-brun (0135-0139)": [f"B59A0{i}.JPG" for i in range(135, 140)],
    "Nicosia-brun (0152-0158)": [f"B59A0{i}.JPG" for i in range(152, 159)],
    "Sousse-taupe (0173-0178)": [f"B59A0{i}.JPG" for i in range(173, 179)]
}

for name, files in sessions_to_test.items():
    colors = []
    for f in files:
        path = os.path.join(dir_in_out, f)
        col = get_average_color(path)
        if col is not None:
            colors.append(col)
    if colors:
        avg_col = np.mean(colors, axis=0)
        print(f"{name:30s} | Avg RGB: ({avg_col[0]:.1f}, {avg_col[1]:.1f}, {avg_col[2]:.1f})")
