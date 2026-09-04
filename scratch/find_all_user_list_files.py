import os

USER_LIST_PATH = r"scratch/filenames_input_4.txt"
TURBOFLOW_ROOT = r"C:\Users\AndronikGruppen\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
# Let's fix the path in case the username is AndronikLindgren
TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    if not os.path.exists(USER_LIST_PATH):
        print(f"User list file not found at: {USER_LIST_PATH}")
        return
        
    with open(USER_LIST_PATH, "r", encoding="utf-8") as f:
        filenames = [line.strip() for line in f if line.strip()]
        
    print(f"Loaded {len(filenames)} filenames to search for.")
    
    # We will build a map of filename to list of paths where it is found
    found_map = {fname: [] for fname in filenames}
    
    print(f"Walking {TURBOFLOW_ROOT} recursively...")
    total_files_scanned = 0
    for dirpath, dirnames, files in os.walk(TURBOFLOW_ROOT):
        for f in files:
            total_files_scanned += 1
            if f in found_map:
                found_map[f].append(os.path.join(dirpath, f))
                
    print(f"Scanned {total_files_scanned} files in total.")
    
    # Let's see how many of the target files were found
    found_count = sum(1 for fname, paths in found_map.items() if paths)
    print(f"Found {found_count} out of {len(filenames)} target files in the turboflow directory tree.")
    
    # Let's group the found files by the subfolder (relative to TURBOFLOW_ROOT)
    folder_groups = {}
    missing_files = []
    
    for fname, paths in found_map.items():
        if not paths:
            missing_files.append(fname)
            continue
            
        for path in paths:
            rel_dir = os.path.relpath(os.path.dirname(path), TURBOFLOW_ROOT)
            if rel_dir not in folder_groups:
                folder_groups[rel_dir] = []
            folder_groups[rel_dir].append((fname, path))
            
    print("\n--- LOCATIONS OF FOUND FILES ---")
    for folder, files_in_folder in sorted(folder_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"Folder: '{folder}' -> Contains {len(files_in_folder)} of the target files.")
        # Print first 5 files as sample
        print("  Sample files:")
        for fname, path in sorted(files_in_folder)[:5]:
            print(f"    - {fname}")
            
    if missing_files:
        print(f"\n--- MISSING FILES ({len(missing_files)}) ---")
        print("These files from your list were not found anywhere in the turboflow tree:")
        for fname in sorted(missing_files)[:10]:
            print(f"  - {fname}")
        if len(missing_files) > 10:
            print(f"  ... and {len(missing_files) - 10} more.")
            
    # Let's output a detailed report as an artifact
    report_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\user_list_locations_report.md"
    with open(report_path, "w", encoding="utf-8") as f_out:
        f_out.write("# Audit of User Paste File Locations\n\n")
        f_out.write(f"We scanned the entire turboflow tree for the **{len(filenames)}** filenames pasted in your log.\n\n")
        f_out.write(f"**Found**: {found_count} files\n")
        f_out.write(f"**Missing**: {len(missing_files)} files\n\n")
        
        f_out.write("## File Count by Folder Location\n\n")
        f_out.write("| Subfolder Path | Count | Description |\n")
        f_out.write("|---|---|---|\n")
        for folder, files_in_folder in sorted(folder_groups.items(), key=lambda x: len(x[1]), reverse=True):
            f_out.write(f"| `{folder}` | {len(files_in_folder)} | Contains matched target files |\n")
            
        f_out.write("\n\n## Detailed Folder Listings\n\n")
        for folder, files_in_folder in sorted(folder_groups.items(), key=lambda x: len(x[1]), reverse=True):
            f_out.write(f"### Subfolder: `{folder}` ({len(files_in_folder)} files)\n")
            f_out.write("| Filename | Full Path |\n")
            f_out.write("|---|---|\n")
            for fname, path in sorted(files_in_folder):
                f_out.write(f"| {fname} | [Link to file](file:///{path.replace('\\', '/')}) |\n")
            f_out.write("\n")
            
    print(f"\nGenerated detailed report artifact at: {report_path}")

if __name__ == "__main__":
    main()
