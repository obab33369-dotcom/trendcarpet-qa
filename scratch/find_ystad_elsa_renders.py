import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering-borttagna")

def scan_folders_for_terms(root, terms):
    if not os.path.exists(root):
        print(f"Directory not found: {root}")
        return []
    
    results = []
    for f in os.listdir(root):
        path = os.path.join(root, f)
        if os.path.isdir(path):
            for term in terms:
                if term.lower() in f.lower():
                    # Count files
                    main_files = [x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x)) and not x.startswith("00_REFERENCE_")]
                    reserv_path = os.path.join(path, "reserv")
                    reserv_files = []
                    if os.path.exists(reserv_path):
                        reserv_files = [x for x in os.listdir(reserv_path) if os.path.isfile(os.path.join(reserv_path, x))]
                    results.append({
                        "folder_name": f,
                        "main_files": main_files,
                        "reserv_files": reserv_files,
                        "path": path
                    })
    return results

def main():
    terms = ["ystad", "elsa", "pinnstol"]
    
    print("=== SCANNING CLEAN DIRECTORY ===")
    clean_results = scan_folders_for_terms(CLEAN_DIR, terms)
    for r in clean_results:
        print(f"\nFolder: {r['folder_name']}")
        print(f"  Main files ({len(r['main_files'])}): {r['main_files'][:10]}")
        print(f"  Reserv files ({len(r['reserv_files'])}): {r['reserv_files'][:10]}")
        
    print("\n=== SCANNING DISCARDED DIRECTORY ===")
    discard_results = scan_folders_for_terms(DISCARD_DIR, terms)
    for r in discard_results:
        print(f"\nFolder: {r['folder_name']}")
        print(f"  Main files ({len(r['main_files'])}): {r['main_files'][:10]}")
        print(f"  Reserv files ({len(r['reserv_files'])}): {r['reserv_files'][:10]}")

if __name__ == "__main__":
    main()
