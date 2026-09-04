import os
from PIL import Image
import numpy as np

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected\artiklar\19791.jpg"

if not os.path.exists(img_path):
    print("Output image not found.")
else:
    with Image.open(img_path) as img:
        img_np = np.array(img.convert('RGB')).astype(np.float32)
        H, W, _ = img_np.shape
        print(f"Image dimensions: {W}x{H}")
        
        # Scan bottom-left region: y from 70% to 95%, x from 5% to 50%
        y_start = int(H * 0.70)
        y_end = int(H * 0.95)
        x_start = int(W * 0.05)
        x_end = int(W * 0.50)
        
        # Check for vertical edge: difference between adjacent columns
        gray = 0.299 * img_np + 0.587 * img_np + 0.114 * img_np
        gray_region = gray[y_start:y_end, x_start:x_end, 0]
        
        # Compute horizontal gradient (diff between column x and x+1)
        grad_x = np.abs(gray_region[:, 1:] - gray_region[:, :-1])
        
        # Find maximum gradient in each row, and see if they align vertically
        max_grad_indices = np.argmax(grad_x, axis=1)
        max_grad_values = np.max(grad_x, axis=1)
        
        # Print rows where gradient is significant (> 10)
        significant_edges = []
        for i in range(len(max_grad_values)):
            if max_grad_values[i] > 15:
                col_idx = x_start + max_grad_indices[i]
                significant_edges.append((y_start + i, col_idx, max_grad_values[i]))
                
        print(f"Found {len(significant_edges)} rows with significant horizontal transitions in bottom-left.")
        if significant_edges:
            # Let's see if the transition columns cluster around a single x value
            cols = [edge[1] for edge in significant_edges]
            from collections import Counter
            c = Counter(cols)
            most_common_cols = c.most_common(5)
            print(f"Most common transition columns (x): {most_common_cols}")
            
            # Print sample values around the most common transition column
            common_x = most_common_cols[0][0]
            print(f"\nSample pixel brightness around column x={common_x} (for y={significant_edges[0][0]}):")
            y_val = significant_edges[0][0]
            row_pixels = gray[y_val, common_x-5:common_x+6, 0]
            print(f"  x range [{common_x-5} to {common_x+5}]: {row_pixels}")
