import os
import glob

def main():
    search_roots = [
        r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures",
        r"C:\Users\AndronikLindgren\Downloads",
        r"C:\Users\AndronikLindgren\Desktop"
    ]
    
    print("Searching for files containing '3340-architectural-digest' or similar patterns...")
    
    found_files = []
    for root in search_roots:
        if not os.path.exists(root):
            print(f"Path does not exist: {root}")
            continue
        print(f"Scanning {root}...")
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if "3340-" in filename or "3339-" in filename or "architectural-digest-styl-320" in filename:
                    full_path = os.path.join(dirpath, filename)
                    found_files.append((filename, full_path))
                    
    if found_files:
        print(f"\nFound {len(found_files)} files:")
        for name, path in found_files:
            print(f"  Name: {name}\n  Path: {path}\n")
    else:
        print("\nNo files found matching the patterns in standard locations.")

if __name__ == "__main__":
    main()
