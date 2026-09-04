import os

SOURCE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering"

def analyze_folders():
    if not os.path.exists(SOURCE_DIR):
        print("Source directory not found.")
        return
        
    folders = [f for f in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, f))]
    
    total_folders = len(folders)
    folders_with_images = 0
    folders_empty = []
    
    image_counts = []
    
    for f in folders:
        path = os.path.join(SOURCE_DIR, f)
        # Count renders (excluding reference image and subfolders)
        render_files = []
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                if not file.startswith("00_REFERENCE_"):
                    render_files.append(file)
                    
        # Also count reserv folder files if exists
        reserv_path = os.path.join(path, "reserv")
        reserv_files_count = 0
        if os.path.exists(reserv_path):
            reserv_files_count = len([file for file in os.listdir(reserv_path) if os.path.isfile(os.path.join(reserv_path, file))])
            
        total_renders = len(render_files) + reserv_files_count
        image_counts.append((f, total_renders, len(render_files), reserv_files_count))
        
        if total_renders > 0:
            folders_with_images += 1
        else:
            folders_empty.append(f)
            
    # Calculate stats
    counts_only = [item[1] for item in image_counts]
    max_count = max(counts_only) if counts_only else 0
    min_count = min(counts_only) if counts_only else 0
    avg_count = sum(counts_only) / len(counts_only) if counts_only else 0
    
    # Sort by total images descending
    image_counts.sort(key=lambda x: x[1], reverse=True)
    
    print("=== DETAILED FOLDER STATISTICS ===")
    print(f"Total folders analyzed: {total_folders}")
    print(f"Folders with >= 1 image: {folders_with_images} ({folders_with_images/total_folders*100:.1f}%)")
    print(f"Folders with 0 images: {len(folders_empty)} ({len(folders_empty)/total_folders*100:.1f}%)")
    print(f"\nImage distribution per folder:")
    print(f"  - Max images in a folder: {max_count}")
    print(f"  - Min images in a folder: {min_count}")
    print(f"  - Average images per folder: {avg_count:.1f}")
    
    print("\nTop 10 folders with the most images:")
    for name, total, main, reserv in image_counts[:10]:
        print(f"  - {name}: {total} total (Main: {main}, reserv: {reserv})")
        
    if folders_empty:
        print(f"\nSample of empty folders (0 images, only reference image) - showing first 15 of {len(folders_empty)}:")
        for name in sorted(folders_empty)[:15]:
            print(f"  - {name}")

if __name__ == "__main__":
    analyze_folders()
