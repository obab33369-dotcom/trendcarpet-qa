import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def count_files():
    if not os.path.exists(DISCARD_DIR):
        print(f"Discard dir {DISCARD_DIR} does not exist.")
        return 0, 0, {}
        
    total_files = 0
    total_folders = 0
    folder_counts = {}
    
    for folder in os.listdir(DISCARD_DIR):
        folder_path = os.path.join(DISCARD_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
            
        total_folders += 1
        count_in_folder = 0
        
        # Check files in folder
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                    count_in_folder += 1
                    total_files += 1
                    
        if count_in_folder > 0:
            folder_counts[folder] = count_in_folder
            
    return total_files, total_folders, folder_counts

if __name__ == "__main__":
    total_files, total_folders, folder_counts = count_files()
    print(f"Total discarded files: {total_files}")
    print(f"Total discarded folders: {total_folders}")
    print("\nTop folders by file count:")
    sorted_folders = sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)
    for f, c in sorted_folders[:15]:
        print(f"  - {f}: {c} files")
