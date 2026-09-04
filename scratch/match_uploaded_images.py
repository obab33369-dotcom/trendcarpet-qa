import os
from PIL import Image
import numpy as np

ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def get_image_hash(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.resize((16, 16)).convert('L')
            data = np.array(img)
            # Simple average hash
            avg = data.mean()
            return (data > avg).astype(int)
    except Exception as e:
        return None

def hash_distance(h1, h2):
    return np.count_nonzero(h1 != h2)

def main():
    uploaded_files = [
        ("Image 1 (Cantilever Corduroy)", os.path.join(ARTIFACTS_DIR, "media__1781178578387.jpg")),
        ("Image 2 (White Spindle)", os.path.join(ARTIFACTS_DIR, "media__1781178587498.jpg"))
    ]
    
    print("Computing hashes for uploaded images...")
    hashes = []
    for label, path in uploaded_files:
        h = get_image_hash(path)
        if h is not None:
            hashes.append((label, h))
            print(f"  Computed hash for {label}")
        else:
            print(f"  Failed to compute hash for {label}")
            
    if not hashes:
        print("No hashes computed. Exiting.")
        return
        
    print("\nScanning OneDrive directories to find matching files...")
    matches = {label: [] for label, _ in hashes}
    
    for root, dirs, files in os.walk(ONEDRIVE_DIR):
        # Skip some folders to speed up
        if "ftp_upload" in root:
            continue
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                path = os.path.join(root, file)
                # Compute hash for this file
                h_file = get_image_hash(path)
                if h_file is not None:
                    for label, h_up in hashes:
                        dist = hash_distance(h_up, h_file)
                        if dist <= 10:  # Very close match
                            matches[label].append((path, dist))
                            
    print("\n=== MATCHING RESULTS ===")
    for label, m_list in matches.items():
        print(f"\nResults for {label}:")
        if not m_list:
            print("  No match found.")
        else:
            # Sort by distance
            m_list.sort(key=lambda x: x[1])
            for path, dist in m_list[:5]:
                # Relative path from ONEDRIVE_DIR
                rel_path = os.path.relpath(path, ONEDRIVE_DIR)
                print(f"  - {rel_path} (Hash Distance: {dist})")

if __name__ == "__main__":
    main()
