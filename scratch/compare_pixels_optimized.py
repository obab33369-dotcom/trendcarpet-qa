import os
import json
from PIL import Image

REF_DIRS = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
]

def get_image_hash(path):
    """Computes a 64-bit Average Hash (aHash) for an image."""
    try:
        img = Image.open(path)
        width, height = img.size
        # Resize to 8x8 and convert to grayscale
        img_small = img.resize((8, 8), Image.Resampling.LANCZOS).convert('L')
        pixels = list(img_small.getdata())
        avg = sum(pixels) / 64
        
        # Build 64-bit integer hash
        hash_val = 0
        for p in pixels:
            hash_val = (hash_val << 1) | (1 if p >= avg else 0)
            
        return {
            "path": path,
            "filename": os.path.basename(path),
            "dimensions": f"{width}x{height}",
            "hash": hash_val,
            "size_bytes": os.path.getsize(path)
        }
    except Exception as e:
        return None

def hamming_distance(h1, h2):
    """Calculates the number of differing bits between two 64-bit hashes."""
    return bin(h1 ^ h2).count('1')

def main():
    print("=== OPTIMIZED PIXEL-LEVEL IMAGE DUPLICATE ANALYSIS ===")
    
    # Scan all files in the reference directories recursively
    all_files = []
    for d in REF_DIRS:
        if not os.path.exists(d):
            continue
        print(f"Scanning directory: {d}...")
        for root, dirs, files in os.walk(d):
            for f in files:
                if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                    all_files.append(os.path.join(root, f))
                
    print(f"Found {len(all_files)} total reference images (recursively).")
    
    # Extract hashes in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    fingerprints = []
    print(f"Extracting hashes in parallel (using 30 threads)...")
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(get_image_hash, p): p for p in all_files}
        completed = 0
        for future in as_completed(futures):
            fp = future.result()
            if fp:
                fingerprints.append(fp)
            completed += 1
            if completed % 100 == 0 or completed == len(all_files):
                print(f"  Processed {completed}/{len(all_files)} images...")
            
    print(f"Successfully loaded and hashed {len(fingerprints)} images.")
    
    # Compare each pair of images using Hamming distance (64-bit XOR)
    duplicates = []
    
    # Visual match threshold: <= 2 bits difference out of 64 bits (approx. 97% similarity)
    # A difference of 0 means 100% visually identical.
    for i in range(len(fingerprints)):
        for j in range(i + 1, len(fingerprints)):
            fp1 = fingerprints[i]
            fp2 = fingerprints[j]
            
            # Skip if they have the exact same path
            if fp1["path"] == fp2["path"]:
                continue
                
            # Calculate Hamming distance (super fast bitwise operation)
            dist = hamming_distance(fp1["hash"], fp2["hash"])
            
            if dist <= 2:
                duplicates.append({
                    "file1": fp1["filename"],
                    "path1": fp1["path"],
                    "dims1": fp1["dimensions"],
                    "file2": fp2["filename"],
                    "path2": fp2["path"],
                    "dims2": fp2["dimensions"],
                    "bit_diff": dist
                })
                
    print(f"\nFound {len(duplicates)} pairs of visual duplicates (similarity > 97%):\n")
    
    import sys
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

    # Sort duplicates by filename
    duplicates = sorted(duplicates, key=lambda x: x["file1"])
    
    # Compile a JSON output of the visual duplicates first
    report_path = r"c:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\visual_duplicates_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(duplicates, f, indent=2, ensure_ascii=False)
    print(f"\nVisual duplicates report saved to: {report_path}")

    print(f"\nFound {len(duplicates)} pairs of visual duplicates (similarity > 97%):\n")
    for dup in duplicates:
        try:
            print(f"DUPLICATE DETECTED:")
            print(f"  File A: {dup['file1']} ({dup['dims1']})")
            print(f"    Path: {dup['path1']}")
            print(f"  File B: {dup['file2']} ({dup['dims2']})")
            print(f"    Path: {dup['path2']}")
            print(f"  Bit Difference: {dup['bit_diff']} / 64")
            print("-" * 60)
        except Exception as e:
            print(f"Error printing a duplicate pair: {e}")

if __name__ == "__main__":
    main()
