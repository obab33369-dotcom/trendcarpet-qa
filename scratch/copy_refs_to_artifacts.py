import os
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec"

def main():
    arvella_folders = [
        "Matta Arvella - Brun (RG01-64)",
        "Matta Arvella - BrunSvart (RG01-66)",
        "Matta Arvella - RödGrön (RG01-65)"
    ]
    
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    copied_files = []
    for f in arvella_folders:
        src_dir = os.path.join(CLEAN_ROOT, f)
        if not os.path.exists(src_dir):
            print(f"Folder not found: {src_dir}")
            continue
            
        for item in os.listdir(src_dir):
            if item.startswith("00_REFERENCE_"):
                src_file = os.path.join(src_dir, item)
                dest_file = os.path.join(ARTIFACTS_DIR, item)
                shutil.copy2(src_file, dest_file)
                print(f"Copied {item} to {dest_file}")
                copied_files.append(item)
                
    # Create the comparison markdown artifact
    md_path = os.path.join(ARTIFACTS_DIR, "arvella_refs_comparison.md")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Arvella Reference Photos Comparison\n\n")
        f.write("Here are the three Arvella reference images currently stored in the consolidated folders:\n\n")
        
        for cf in copied_files:
            sku = cf.replace("00_REFERENCE_", "").replace(".jpg", "")
            f.write(f"## Reference for {sku}\n")
            f.write(f"![Reference {sku}](file:///{os.path.join(ARTIFACTS_DIR, cf).replace('\\', '/')})\n\n")
            
    print(f"Created comparison artifact at {md_path}")

if __name__ == "__main__":
    main()
