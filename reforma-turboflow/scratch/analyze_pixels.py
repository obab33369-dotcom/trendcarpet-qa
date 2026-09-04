from PIL import Image
import numpy as np

orig_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\YD-G18-W_orig.jpg"
corr_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\YD-G18-W_corrected.jpg"

with Image.open(orig_path) as img:
    W, H = img.size
    img_np = np.array(img)
    print("Original image:")
    print(f"Dimensions: W={W}, H={H}")
    # Print the average intensity of the bottom rows
    for y in range(H - 60, H, 10):
        row = img_np[y, :, :]
        row_mean = np.mean(row, axis=(0,1))
        row_min = np.min(row)
        print(f"Row y={y}: mean intensity = {row_mean:.1f}, min intensity = {row_min}")

with Image.open(corr_path) as img:
    W, H = img.size
    img_np = np.array(img)
    print("\nCorrected image:")
    print(f"Dimensions: W={W}, H={H}")
    for y in range(H - 120, H, 15):
        row = img_np[y, :, :]
        row_mean = np.mean(row, axis=(0,1))
        row_min = np.min(row)
        print(f"Row y={y}: mean intensity = {row_mean:.1f}, min intensity = {row_min}")
