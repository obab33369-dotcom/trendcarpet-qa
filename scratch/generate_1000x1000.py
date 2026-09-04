import os
from PIL import Image

def main():
    base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides"
    src_dir = os.path.join(base_dir, "Batch 2 - Processed (1500x1500)")
    dest_dir = os.path.join(base_dir, "Batch 2 - Processed (1000x1000)")
    
    if not os.path.exists(src_dir):
        print(f"Error: Source directory {src_dir} does not exist.")
        return
        
    os.makedirs(dest_dir, exist_ok=True)
    print(f"Creating 1000x1000px images from {src_dir} to {dest_dir}...")
    
    files = [f for f in os.listdir(src_dir) if f.lower().endswith('.jpg')]
    total = len(files)
    
    for i, f in enumerate(files, 1):
        src_path = os.path.join(src_dir, f)
        dest_path = os.path.join(dest_dir, f)
        
        try:
            with Image.open(src_path) as img:
                # Resize to 1000x1000
                resized = img.resize((1000, 1000), Image.Resampling.LANCZOS)
                # Save as JPEG
                resized.save(dest_path, "JPEG", quality=90)
            print(f"[{i}/{total}] Resized: {f}")
        except Exception as e:
            print(f"[{i}/{total}] Error resizing {f}: {e}")
            
    print("\nGeneration of 1000x1000px images is complete!")

if __name__ == "__main__":
    main()
