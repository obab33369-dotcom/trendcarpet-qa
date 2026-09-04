import os

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DST = os.path.join(TURBOFLOW_ROOT, "Reforma-interiörer-ny-sortering")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def main():
    carpet_folders = [d for d in os.listdir(CLEAN_DST) if os.path.isdir(os.path.join(CLEAN_DST, d)) and is_carpet(d)]
    
    print("Checking carpet folders in destination:")
    no_root_renders = 0
    total_folders = 0
    for folder in carpet_folders:
        path = os.path.join(CLEAN_DST, folder)
        files = os.listdir(path)
        
        images_in_root = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and not f.startswith('00_REFERENCE_')]
        
        reserv_path = os.path.join(path, "reserv")
        has_reserv_dir = os.path.exists(reserv_path) and os.path.isdir(reserv_path)
        images_in_reserv = []
        if has_reserv_dir:
            images_in_reserv = [f for f in os.listdir(reserv_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            
        print(f"  {folder}: Root renders={len(images_in_root)}, Reserv renders={len(images_in_reserv)}, Has reserv dir={has_reserv_dir}")
        if len(images_in_root) == 0:
            no_root_renders += 1
        total_folders += 1
        
    print(f"\nSummary: Total carpet folders checked: {total_folders}")
    print(f"Carpet folders with ZERO renders in root: {no_root_renders}")

if __name__ == "__main__":
    main()
