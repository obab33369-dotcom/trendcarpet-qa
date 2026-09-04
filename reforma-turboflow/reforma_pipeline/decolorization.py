import numpy as np
from PIL import Image

def clean_offwhite_background(img, bg_color, tolerance=15.0, blend_range=80.0, highlight_threshold=None, highlight_factor=None):
    """
    Cleans off-white backgrounds (e.g. from renders or upscaled files) to pure white (#FFFFFF)
    while preserving natural shadows and desaturating them.
    Supports adjustable tolerance and blend_range for self-correcting QA loop.
    Applies a soft vignette-fade to white at the outer 5% edges to clean up corners.
    """
    img_arr = np.array(img.convert('RGB')).astype(np.float32)
    bg_color = np.array(bg_color).astype(np.float32)
    
    # Calculate pixel distance from bg_color
    diff = np.sum(np.abs(img_arr - bg_color), axis=-1)
    
    # Soft mask: 0.0 at bg_color, 1.0 far away
    # Using dynamic tolerance and transition width (blend_range)
    color_mask = np.clip((diff - tolerance) / max(1.0, blend_range), 0.0, 1.0)
    color_mask = np.expand_dims(color_mask, axis=-1)
    
    # Normalize/brighten to map bg_color to 255
    scale = 255.0 / np.clip(bg_color - 2.0, 1.0, 255.0)
    normalized = np.clip(img_arr * scale, 0, 255)
    
    # Desaturate
    gray = 0.299 * normalized[:,:,0] + 0.587 * normalized[:,:,1] + 0.114 * normalized[:,:,2]
    gray_img = np.stack([gray, gray, gray], axis=-1)
    
    # Blend: desaturated normalized for bg/shadow, normalized color for product
    final_arr = normalized * color_mask + gray_img * (1.0 - color_mask)
    
    # Apply highlights reduction selectively to product area
    if highlight_threshold is not None and highlight_factor is not None:
        adjusted_arr = final_arr.copy()
        mask = adjusted_arr > highlight_threshold
        adjusted_arr[mask] = highlight_threshold + (adjusted_arr[mask] - highlight_threshold) * highlight_factor
        final_arr = adjusted_arr * color_mask + final_arr * (1.0 - color_mask)
    
    # Apply a soft vignette-fade to pure white at the outer 5% edges, but ONLY pull pixels
    # that are already near-white toward white. This cleans up off-white corner gradients/
    # dirt WITHOUT artificially fading genuine shadows that legitimately reach the frame
    # edge — the webshop accepts a shadow running off-frame, but it must look like a
    # natural crop, not a faded "cut-out" edge.
    h, w, _ = final_arr.shape
    vignette = 0.05
    edge_w = int(w * vignette)
    edge_h = int(h * vignette)
    
    if edge_w > 0 and edge_h > 0:
        grad_x = np.clip(np.arange(w, dtype=np.float32) / edge_w, 0.0, 1.0)
        grad_x = np.minimum(grad_x, np.clip((w - 1 - np.arange(w, dtype=np.float32)) / edge_w, 0.0, 1.0))
        
        grad_y = np.clip(np.arange(h, dtype=np.float32) / edge_h, 0.0, 1.0)
        grad_y = np.minimum(grad_y, np.clip((h - 1 - np.arange(h, dtype=np.float32)) / edge_h, 0.0, 1.0))
        
        vignette_mask = np.outer(grad_y, grad_x)        # 1.0 = keep, 0.0 = pull to white
        pull_to_white = 1.0 - vignette_mask
        
        # Gate the whitening so it only affects near-white pixels; real shadow/product
        # pixels (luma < 225) are left completely untouched.
        luma_final = 0.299 * final_arr[:, :, 0] + 0.587 * final_arr[:, :, 1] + 0.114 * final_arr[:, :, 2]
        near_white = np.clip((luma_final - 225.0) / 20.0, 0.0, 1.0)  # 0 below 225, 1 at/above 245
        pull_to_white = pull_to_white * near_white
        pull_3d = np.expand_dims(pull_to_white, axis=-1)
        
        white_img = np.ones_like(final_arr) * 255.0
        final_arr = final_arr * (1.0 - pull_3d) + white_img * pull_3d
        
    return Image.fromarray(np.round(final_arr).astype(np.uint8))


