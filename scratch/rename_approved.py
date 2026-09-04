import os
import json

def load_mapping():
    path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers.json"
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create a lookup map: base_name (lowercase) -> number
    lookup = {}
    for filename, val in data.items():
        if "error" in val:
            continue
        base = os.path.splitext(filename)[0].lower()
        lookup[base] = str(val.get("number", "")).strip()
    return lookup

def run_rename(dry_run=True):
    lookup = load_mapping()
    if not lookup:
        print("Error: No valid mapping loaded from JSON.")
        return
        
    parent_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10"
    dirs = [
        os.path.join(parent_dir, "Batch 2 - Approved (Original Size)"),
        os.path.join(parent_dir, "Batch 2 - Approved (1500x1500)")
    ]
    
    total_renamed = 0
    total_skipped = 0
    
    for d in dirs:
        if not os.path.exists(d):
            print(f"Directory not found: {d}")
            continue
            
        print(f"\n--- Processing Directory: {os.path.basename(d)} ---")
        files = [f for f in os.listdir(d) if f.lower().endswith('.jpg')]
        
        for f in files:
            # Check if it is already renamed (e.g. starts with digits followed by a hyphen)
            # Find the base code (e.g., AHIN4169)
            parts = f.split('-')
            
            # If the first part is a digit, it might already be renamed
            if parts[0].isdigit():
                print(f"Already renamed: {f}")
                total_skipped += 1
                continue
                
            base_code = parts[0]
            lookup_key = base_code.lower()
            
            if lookup_key in lookup:
                num = lookup[lookup_key]
                if not num:
                    print(f"Skipping (no number in mapping): {f}")
                    total_skipped += 1
                    continue
                    
                new_name = f"{num}-{f}"
                old_path = os.path.join(d, f)
                new_path = os.path.join(d, new_name)
                
                if dry_run:
                    print(f"[DRY-RUN] Rename: '{f}' -> '{new_name}'")
                else:
                    try:
                        os.rename(old_path, new_path)
                        print(f"Renamed: '{f}' -> '{new_name}'")
                    except Exception as e:
                        print(f"Error renaming '{f}': {e}")
                total_renamed += 1
            else:
                print(f"Warning: No number found in mapping for code '{base_code}' in file '{f}'")
                total_skipped += 1
                
    print(f"\nSummary: {total_renamed} files to rename, {total_skipped} files skipped/already renamed.")

def main():
    print("=== STARTING ACTIVE RENAMING ===")
    run_rename(dry_run=False)

if __name__ == "__main__":
    main()
