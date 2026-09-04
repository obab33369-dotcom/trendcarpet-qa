import os
import hashlib
import json
from PIL import Image

REF_DIRS = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
]

def get_image_fingerprint(path):
    try:
        img = Image.open(path)
        width, height = img.size
        # Resize to 32x32 and convert to grayscale for visual hashing
        img_small = img.resize((32, 32)).convert('L')
        pixels = list(img_small.getdata())
        return {
            "path": path,
            "filename": os.path.basename(path),
            "dimensions": f"{width}x{height}",
            "pixels": pixels,
            "size_bytes": os.path.getsize(path)
        }
    except Exception as e:
        return None

def calculate_similarity(pixels1, pixels2):
    # Mean Absolute Error (MAE)
    mae = sum(abs(p1 - p2) for p1, p2 in zip(pixels1, pixels2)) / len(pixels1)
    return mae

def main():
    print("=== PIXEL-LEVEL IMAGE SIMILARITY ANALYSIS ===")
    
    # Scan all files in the reference directories
    all_files = []
    for d in REF_DIRS:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                path = os.path.join(d, f)
                all_files.append(path)
                
    print(f"Found {len(all_files)} total reference images across source folders.")
    
    # Extract fingerprints (dimensions and pixel data)
    fingerprints = []
    for p in all_files:
        fp = get_image_fingerprint(p)
        if fp:
            fingerprints.append(fp)
            
    print(f"Successfully processed {len(fingerprints)} images.")
    
    # Compare each pair of images to find visual duplicates
    duplicates = []
    checked_pairs = set()
    
    for i in range(len(fingerprints)):
        for j in range(i + 1, len(fingerprints)):
            fp1 = fingerprints[i]
            fp2 = fingerprints[j]
            
            # Skip if they have the exact same path (shouldn't happen)
            if fp1["path"] == fp2["path"]:
                continue
                
            # If filenames are the same, they might be in different source folders
            if fp1["filename"] == fp2["filename"]:
                continue
                
            # Calculate pixel similarity
            mae = calculate_similarity(fp1["pixels"], fp2["pixels"])
            
            # An MAE of 0 means identical pixels. 
            # We use a threshold of 3.0 to capture slightly compressed or resized versions of the same image.
            if mae < 3.0:
                duplicates.append({
                    "file1": fp1["filename"],
                    "path1": fp1["path"],
                    "dims1": fp1["dimensions"],
                    "file2": fp2["filename"],
                    "path2": fp2["path"],
                    "dims2": fp2["dimensions"],
                    "mae": mae
                })
                
    print(f"\nFound {len(duplicates)} pairs of visual duplicates (pixel similarity > 98.8%):\n")
    
    # Sort duplicates by filename for readability
    duplicates = sorted(duplicates, key=lambda x: x["file1"])
    
    for dup in duplicates:
        print(f"DUPLICATE DETECTED:")
        print(f"  File A: {dup['file1']} ({dup['dims1']})")
        print(f"    Path: {dup['path1']}")
        print(f"  File B: {dup['file2']} ({dup['dims2']})")
        print(f"    Path: {dup['path2']}")
        print(f"  Pixel Difference (MAE): {dup['mae']:.2f}")
        print("-" * 60)
        
    # Compile a JSON output of the visual duplicates
    with open(r"c:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\visual_duplicates_report.json", "w", encoding="utf-8") as f:
        json.dump(duplicates, f, indent=2, ensure_ascii=False)
    print("\nVisual duplicates report saved to: C:\\Users\\AndronikLindgren\\OneDrive - CaMa Gruppen AB\\Pictures\\turboflow\\visual_duplicates_report.json")

if __name__ == "__main__":
    main()
