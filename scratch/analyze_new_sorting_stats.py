import os

TARGET_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-Full-Catalog-sortering"

def main():
    if not os.path.exists(TARGET_DIR):
        print("Folder not found.")
        return
        
    folders = [f for f in os.listdir(TARGET_DIR) if os.path.isdir(os.path.join(TARGET_DIR, f))]
    total_folders = len(folders)
    
    folders_with_renders = 0
    empty_folders = []
    
    image_counts = []
    
    for f in folders:
        path = os.path.join(TARGET_DIR, f)
        # Count renders (excluding reference image and subfolders)
        render_files = []
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                if not file.startswith("00_REFERENCE_"):
                    render_files.append(file)
                    
        # Count reserv folder files
        reserv_path = os.path.join(path, "reserv")
        reserv_files_count = 0
        if os.path.exists(reserv_path):
            reserv_files_count = len([file for file in os.listdir(reserv_path) if os.path.isfile(os.path.join(reserv_path, file))])
            
        total_renders = len(render_files) + reserv_files_count
        image_counts.append((f, total_renders, len(render_files), reserv_files_count))
        
        if total_renders > 0:
            folders_with_renders += 1
        else:
            empty_folders.append(f)
            
    # Calculate stats
    counts_only = [item[1] for item in image_counts]
    max_count = max(counts_only) if counts_only else 0
    min_count = min(counts_only) if counts_only else 0
    avg_count = sum(counts_only) / len(counts_only) if counts_only else 0
    
    print("=== NEW SORTING FOLDER STATISTICS ===")
    print(f"Total folders analyzed: {total_folders}")
    print(f"Folders with >= 1 render: {folders_with_renders} ({folders_with_renders/total_folders*100:.1f}%)")
    print(f"Folders with 0 renders (only reference image): {len(empty_folders)} ({len(empty_folders)/total_folders*100:.1f}%)")
    print(f"\nImage distribution per folder:")
    print(f"  - Max renders in a folder: {max_count}")
    print(f"  - Min renders in a folder: {min_count}")
    print(f"  - Average renders per folder: {avg_count:.1f}")
    
    # Sort by total images descending
    image_counts.sort(key=lambda x: x[1], reverse=True)
    print("\nTop 10 folders with the most renders:")
    for name, total, main, reserv in image_counts[:10]:
        print(f"  - {name}: {total} total (Main: {main}, reserv: {reserv})")
        
    if empty_folders:
        print(f"\nList of empty folders ({len(empty_folders)}):")
        for name in sorted(empty_folders):
            print(f"  - {name}")
    else:
        print("\nAll folders contain at least one render!")

if __name__ == "__main__":
    main()
