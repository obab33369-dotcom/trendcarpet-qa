import os

SOURCE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering"

def main():
    if not os.path.exists(SOURCE_DIR):
        print("Source directory not found.")
        return
        
    folders = [f for f in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, f))]
    
    empty_folders_info = []
    
    for f in folders:
        path = os.path.join(SOURCE_DIR, f)
        all_files = os.listdir(path)
        
        # Subfolders
        subfolders = [d for d in all_files if os.path.isdir(os.path.join(path, d))]
        
        # Files directly in the folder
        files = [file for file in all_files if os.path.isfile(os.path.join(path, file))]
        
        # Check if there are renders
        render_files = [file for file in files if not file.startswith("00_REFERENCE_")]
        
        # Check if there is a reserv folder
        reserv_path = os.path.join(path, "reserv")
        reserv_files = []
        if os.path.exists(reserv_path):
            reserv_files = [file for file in os.listdir(reserv_path) if os.path.isfile(os.path.join(reserv_path, file))]
            
        total_renders = len(render_files) + len(reserv_files)
        
        if total_renders == 0:
            empty_folders_info.append({
                "name": f,
                "files": files,
                "subfolders": subfolders
            })
            
    print(f"Found {len(empty_folders_info)} empty folders:")
    for idx, info in enumerate(sorted(empty_folders_info, key=lambda x: x["name"]), 1):
        print(f"{idx}. {info['name']}")
        print(f"   Files: {info['files']}")
        print(f"   Subfolders: {info['subfolders']}")

if __name__ == "__main__":
    main()
