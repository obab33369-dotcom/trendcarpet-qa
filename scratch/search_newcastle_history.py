import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_files_for_keyword(directory, keyword):
    print(f"\n--- Searching for '{keyword}' in {directory} ---")
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(('.py', '.log', '.txt', '.md')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        if keyword.lower() in content.lower():
                            print(f"Found in: {os.path.relpath(path, directory)}")
                except Exception:
                    pass

def main():
    # Check if exists in discard root
    newcastle_folder = "Bokhylla Newcastle Svart (NEWCASTLE-BLACK)"
    discard_path = os.path.join(DISCARD_ROOT, newcastle_folder)
    print(f"Discard folder exists: {os.path.exists(discard_path)}")
    if os.path.exists(discard_path):
        print(f"Discard folder contents: {os.listdir(discard_path)}")
        reserv_path = os.path.join(discard_path, "reserv")
        if os.path.exists(reserv_path):
            print(f"Discard folder reserv contents: {os.listdir(reserv_path)}")
            
    # Search python files for Newcastle
    search_files_for_keyword(PROJECT_DIR, "newcastle")
    search_files_for_keyword(os.path.join(PROJECT_DIR, "scratch"), "newcastle")

if __name__ == "__main__":
    main()
