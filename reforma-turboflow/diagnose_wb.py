from PIL import Image
import numpy as np

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\Refoma chair\1 Stol _Astrid_ - Vitpigmenterad\1 Stol _Astrid_ - Vitpigmenterad-01-1-W.jpg"
with Image.open(img_path) as img:
    img_rgb = img.convert('RGB')
    arr = np.array(img_rgb)
    h, w, _ = arr.shape
    print(f"Image shape: {h}x{w}")
    
    # Check borders
    top_border = arr[0, :, :]
    bottom_border = arr[-1, :, :]
    left_border = arr[:, 0, :]
    right_border = arr[:, -1, :]
    
    print("Top border mean:", np.mean(top_border, axis=0))
    print("Bottom border mean:", np.mean(bottom_border, axis=0))
    print("Left border mean:", np.mean(left_border, axis=0))
    print("Right border mean:", np.mean(right_border, axis=0))
    
    # Test our robust function
    # Define 4 corner patches of size 10x10, inset by 10px to avoid 1px black edges
    patches = [
        arr[10:20, 10:20],
        arr[10:20, -20:-10],
        arr[-20:-10, 10:20],
        arr[-20:-10, -20:-10]
    ]
    means = [np.mean(pat, axis=(0,1)) for pat in patches]
    print("Corner means:", means)
    means.sort(key=lambda c: np.sum(c))
    bg_color = np.mean(means[1:], axis=0)
    bg_mean = np.mean(bg_color)
    print(f"Robust background: mean={bg_mean}, color={bg_color}")
    
    # Check thresholding
    diff = np.sum(np.abs(arr - bg_color), axis=-1)
    mask = (diff < 25) & (arr[:,:,0] > 180) & (arr[:,:,1] > 180) & (arr[:,:,2] > 180)
    arr_cleaned = arr.copy()
    arr_cleaned[mask] = [255, 255, 255]
    print(f"Mask True pixels: {np.sum(mask)}")
    
    # Check pixels in output
    out_img = Image.open("test_new_pipeline_chair_armchair_0.jpg")
    out_arr = np.array(out_img.convert("RGB"))
    print("Output corners top-left 5x5:")
    print(out_arr[0:5, 0:5])
    print("Output corners bottom-right 5x5:")
    print(out_arr[-5:, -5:])
    
    non_white = np.argwhere(np.any(out_arr < 254, axis=-1))
    print("Non-white pixel count in output:", non_white.shape[0])
    if non_white.shape[0] > 0:
        y_min, x_min = non_white.min(axis=0)
        y_max, x_max = non_white.max(axis=0)
        print(f"Non-white bbox: y_min={y_min}, y_max={y_max}, x_min={x_min}, x_max={x_max}")
