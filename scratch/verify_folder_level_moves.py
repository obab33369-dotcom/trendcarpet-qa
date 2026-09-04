import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
LOG_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\tasks\task-1730.log"

def main():
    if not os.path.exists(LOG_PATH):
        print("Log not found.")
        return
        
    # We will look for keep log lines and scan the directories
    print("=== VERIFYING FOLDER-LEVEL MOVES ===")
    
    # Read the log lines
    logged_files = []
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r'\[KEEP\] Moving (.*?) back to clean folder\.\.\.', line)
            if m:
                logged_files.append(m.group(1).strip())
                
    if not logged_files:
        print("No keep moves found in log.")
        return
        
    unique_files = list(dict.fromkeys(logged_files))[-5:] # Check the last 5 files
    
    for fname in unique_files:
        print(f"\nChecking file: {fname}")
        # Find where it is in CLEAN_DIR
        clean_paths = []
        for root, dirs, files in os.walk(CLEAN_DIR):
            if fname in files:
                clean_paths.append(root)
                
        # Find where it is in DISCARD_DIR
        discard_paths = []
        for root, dirs, files in os.walk(DISCARD_DIR):
            if fname in files:
                discard_paths.append(root)
                
        print(f"  - Currently in CLEAN folders: {[os.path.basename(p) for p in clean_paths]}")
        print(f"  - Currently in DISCARD folders: {[os.path.basename(p) for p in discard_paths]}")
        
        # Verify that for at least one folder where it is in CLEAN, it is NOT in DISCARD
        verified = False
        for cp in clean_paths:
            folder_name = os.path.basename(cp)
            # Check if this folder name is in discard paths
            is_in_discard = any(os.path.basename(dp) == folder_name for dp in discard_paths)
            if not is_in_discard:
                print(f"  -> [SUCCESS] Successfully moved out of discard folder '{folder_name}' to clean folder '{folder_name}'!")
                verified = True
                
        if not verified:
            print("  -> [ERROR] Not verified at folder level!")

if __name__ == "__main__":
    main()
