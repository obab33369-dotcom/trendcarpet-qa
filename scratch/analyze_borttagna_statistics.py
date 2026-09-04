import os

BORTTAGNA_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering-borttagna"
SOURCE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering"

def main():
    # Source stats
    total_main_renders = 0
    total_reserv_renders = 0
    source_folders_count = 0
    
    if os.path.exists(SOURCE_DIR):
        source_folders = [f for f in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, f))]
        source_folders_count = len(source_folders)
        for f in source_folders:
            path = os.path.join(SOURCE_DIR, f)
            for file in os.listdir(path):
                if os.path.isfile(os.path.join(path, file)) and not file.startswith("00_REFERENCE_"):
                    total_main_renders += 1
            reserv_path = os.path.join(path, "reserv")
            if os.path.exists(reserv_path):
                for file in os.listdir(reserv_path):
                    if os.path.isfile(os.path.join(reserv_path, file)):
                        total_reserv_renders += 1

    # Borttagna stats
    total_borttagna_folders = 0
    total_borttagna_main = 0
    total_borttagna_reserv = 0
    
    if os.path.exists(BORTTAGNA_DIR):
        borttagna_folders = [f for f in os.listdir(BORTTAGNA_DIR) if os.path.isdir(os.path.join(BORTTAGNA_DIR, f))]
        total_borttagna_folders = len(borttagna_folders)
        for f in borttagna_folders:
            path = os.path.join(BORTTAGNA_DIR, f)
            for file in os.listdir(path):
                if os.path.isfile(os.path.join(path, file)) and not file.startswith("00_REFERENCE_"):
                    total_borttagna_main += 1
            reserv_path = os.path.join(path, "reserv")
            if os.path.exists(reserv_path):
                for file in os.listdir(reserv_path):
                    if os.path.isfile(os.path.join(reserv_path, file)):
                        total_borttagna_reserv += 1
                        
    print("=== SUMMARY STATISTICS ===")
    print("Reforma-interiörer-ny-sortering (Cleaned / Kept):")
    print(f"  - Total Product Folders: {source_folders_count}")
    print(f"  - Main Renders: {total_main_renders}")
    print(f"  - Reserv Renders: {total_reserv_renders}")
    print(f"  - Total Clean Renders Kept: {total_main_renders + total_reserv_renders}")
    
    print("\nReforma-interiörer-ny-sortering-borttagna (Filtered / Discarded):")
    print(f"  - Discarded Folders: {total_borttagna_folders}")
    print(f"  - Discarded Main Renders: {total_borttagna_main}")
    print(f"  - Discarded Reserv Renders: {total_borttagna_reserv}")
    print(f"  - Total Discarded Renders: {total_borttagna_main + total_borttagna_reserv}")
    
    grand_total = total_main_renders + total_reserv_renders + total_borttagna_main + total_borttagna_reserv
    print(f"\nGrand Total Processed Renders: {grand_total}")
    if grand_total > 0:
        print(f"  - Keep Rate: {(total_main_renders + total_reserv_renders)/grand_total*100:.1f}%")
        print(f"  - Discard Rate: {(total_borttagna_main + total_borttagna_reserv)/grand_total*100:.1f}%")

if __name__ == "__main__":
    main()
