import os
import numpy as np
from PIL import Image

src_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Pall 'Marcos' - Vit (1400042)\artiklar\1400042.jpg"
brain_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b"

test_files = {
    "original": src_path,
    "reduced_180_0.5": os.path.join(brain_dir, "marcos_cleaned_reduced_180_05.jpg"),
    "reduced_170_0.4": os.path.join(brain_dir, "marcos_cleaned_reduced_170_04.jpg"),
    "reduced_160_0.3": os.path.join(brain_dir, "marcos_cleaned_reduced_160_03.jpg")
}

def analyze_image(path, name):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
        
    img = Image.open(path).convert('RGB')
    arr = np.array(img)
    
    # We define the product area roughly by finding pixels that are not close to the corner background.
    # Corner background is roughly (255, 255, 255) for cleaned ones, or (245, 245, 245) for original.
    # Let's find pixels that are darker than 254 in the middle of the image.
    # To be consistent, let's take a center crop (rows 400 to 1600, cols 400 to 1600)
    h, w, _ = arr.shape
    crop = arr[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8), :]
    
    # Product pixels are those where max(R,G,B) < 255 (not background)
    luma = 0.299 * crop[:,:,0] + 0.587 * crop[:,:,1] + 0.114 * crop[:,:,2]
    
    # Let's calculate the statistics of luma values below 254 (product pixels)
    prod_pixels = luma[luma < 254]
    
    if prod_pixels.size == 0:
        print(f"{name}: No product pixels detected.")
        return
        
    mean_val = np.mean(prod_pixels)
    max_val = np.max(prod_pixels)
    pct_very_bright = np.sum(prod_pixels > 245) / prod_pixels.size * 100
    pct_almost_white = np.sum(prod_pixels > 250) / prod_pixels.size * 100
    
    print(f"{name}:")
    print(f"  Count of product pixels: {prod_pixels.size}")
    print(f"  Average brightness:      {mean_val:.1f}")
    print(f"  Max brightness:          {max_val:.1f}")
    print(f"  % of pixels > 245:       {pct_very_bright:.1f}%")
    print(f"  % of pixels > 250:       {pct_almost_white:.1f}%")

if __name__ == "__main__":
    for name, path in test_files.items():
        analyze_image(path, name)
