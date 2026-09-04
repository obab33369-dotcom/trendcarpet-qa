import os
import sys
import re

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SORTERAT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel"
UPSCALED_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"

def rename_in_directory(root_dir):
    if not os.path.exists(root_dir):
        print(f"Warning: Directory not found: {root_dir}")
        return
        
    print(f"\nScanning directory: {root_dir}")
    categories = sorted([d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])
    
    total_renamed = 0
    total_errors = 0
    
    for cat in categories:
        cat_path = os.path.join(root_dir, cat)
        # Create underscored prefix from folder name
        prefix = cat.replace(" ", "_")
        
        files = os.listdir(cat_path)
        for f in files:
            # Skip reference photos and already renamed ones
            if f.startswith("00_ORIGINAL_") or f.endswith("-IN.png") or f.endswith("-IN.jpg") or f.endswith("-IN.webp"):
                continue
                
            # Only match renders (which start with 3 digits and a hyphen, e.g. "093-")
            if re.match(r"^\d{3}-", f):
                base, ext = os.path.splitext(f)
                
                # Extract the last part after the last hyphen (which contains prompt number + suffix, e.g. '093b')
                parts = base.split('-')
                if not parts:
                    continue
                suffix = parts[-1]
                
                # Construct new clean filename
                new_filename = f"{prefix}-{suffix}-IN{ext}"
                
                src_path = os.path.join(cat_path, f)
                dest_path = os.path.join(cat_path, new_filename)
                
                try:
                    os.rename(src_path, dest_path)
                    total_renamed += 1
                except Exception as e:
                    print(f"   Error renaming '{f}' to '{new_filename}' in '{cat}': {e}")
                    total_errors += 1
                    
    print(f"Successfully renamed {total_renamed} render files in: {os.path.basename(root_dir)}")
    if total_errors > 0:
        print(f"Errors encountered: {total_errors}")

def main():
    print("==================================================")
    print("        RENAMING RENDERS TO PRODUCT CODES         ")
    print("==================================================")
    
    rename_in_directory(SORTERAT_DIR)
    rename_in_directory(UPSCALED_DIR)
    
    print("==================================================")
    print("              RENAMING COMPLETED!                 ")
    print("==================================================")

if __name__ == "__main__":
    main()
