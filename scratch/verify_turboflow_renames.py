import os
import re

CLEAN_DST = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering"
DISCARD_DST = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering-borttagna"

def get_folder_base_name(folder_name):
    base = re.sub(r'\s*\([^)]+\)\s*$', '', folder_name)
    base = re.sub(r'([a-zåäö])([A-ZÅÄÖ])', r'\1-\2', base)
    cleaned = []
    for char in base:
        if char.isalnum() or char in '-_':
            cleaned.append(char)
        else:
            cleaned.append('-')
    base = "".join(cleaned)
    base = re.sub(r'-+', '-', base)
    return base.strip('-')

def check_dir(dir_path, name_label):
    if not os.path.exists(dir_path):
        print(f"Directory {name_label} not found at: {dir_path}")
        return
        
    print(f"\nChecking directory {name_label}...")
    folders = [f for f in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, f))]
    
    total_files = 0
    total_references = 0
    total_renders = 0
    incorrect_names = []
    
    for folder in folders:
        folder_path = os.path.join(dir_path, folder)
        expected_base = get_folder_base_name(folder)
        
        # Check files in folder root
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                if item == "reserv":
                    # Check reserv files
                    for r_item in os.listdir(item_path):
                        r_item_path = os.path.join(item_path, r_item)
                        if os.path.isfile(r_item_path):
                            total_files += 1
                            if r_item.startswith("00_REFERENCE_"):
                                total_references += 1
                            else:
                                total_renders += 1
                                # Verify name
                                if not r_item.startswith(expected_base):
                                    incorrect_names.append(f"{folder}/reserv/{r_item} (expected prefix: {expected_base})")
                                elif not re.search(r'-\d+-\d+\.\w+$', r_item) and not re.search(r'-[^-]+\.\w+$', r_item):
                                    incorrect_names.append(f"{folder}/reserv/{r_item} (invalid tracking code format)")
                continue
                
            if os.path.isfile(item_path):
                total_files += 1
                if item.startswith("00_REFERENCE_"):
                    total_references += 1
                else:
                    total_renders += 1
                    # Verify name
                    if not item.startswith(expected_base):
                        incorrect_names.append(f"{folder}/{item} (expected prefix: {expected_base})")
                    elif not re.search(r'-\d+-\d+\.\w+$', item) and not re.search(r'-[^-]+\.\w+$', item):
                        incorrect_names.append(f"{folder}/{item} (invalid tracking code format)")
                        
    print(f"Summary for {name_label}:")
    print(f"  - Total subfolders: {len(folders)}")
    print(f"  - Total files scanned: {total_files}")
    print(f"  - Total reference images: {total_references}")
    print(f"  - Total render images: {total_renders}")
    print(f"  - Incorrectly named renders: {len(incorrect_names)}")
    if incorrect_names:
        print("    Examples of incorrect names (up to 10):")
        for name in incorrect_names[:10]:
            print(f"      - {name}")
    else:
        print("    All renders named correctly!")

def main():
    check_dir(CLEAN_DST, "CLEAN_DST")
    check_dir(DISCARD_DST, "DISCARD_DST")

if __name__ == "__main__":
    main()
