import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
LOG_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\tasks\task-1730.log"

def main():
    if not os.path.exists(LOG_PATH):
        print("Log file not found.")
        return
        
    print("=== VERIFYING TODAY'S MOVED FILES ===")
    
    # Read moves from log
    moved_actions = []
    # Match: [KEEP] Moving 2681-architectural-digest-styl-027.png back to clean folder...
    # (Note: sometimes the folder name is not on the same line, but let's parse the filenames)
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r'\[KEEP\] Moving (.*?) back to clean folder\.\.\.', line)
            if m:
                filename = m.group(1).strip()
                moved_actions.append(filename)
                
    print(f"Total keep actions logged in server: {len(moved_actions)}")
    if not moved_actions:
        print("No keep actions logged yet.")
        return
        
    # We want to check the last 10 filenames that were logged
    unique_filenames = list(dict.fromkeys(moved_actions))[-10:]
    
    print("\nVerifying the last 10 approved files on OneDrive:")
    success_count = 0
    for fname in unique_filenames:
        # Scan CLEAN_DIR to find if fname exists
        found_in_clean = None
        for root, dirs, files in os.walk(CLEAN_DIR):
            if fname in files:
                found_in_clean = os.path.join(root, fname)
                break
                
        # Scan DISCARD_DIR to check if it's gone
        found_in_discard = None
        for root, dirs, files in os.walk(DISCARD_DIR):
            if fname in files:
                found_in_discard = os.path.join(root, fname)
                break
                
        if found_in_clean and not found_in_discard:
            rel_clean = os.path.relpath(found_in_clean, CLEAN_DIR)
            print(f"  [OK] {fname}")
            print(f"       -> Successfully moved to CLEAN: {rel_clean}")
            print(f"       -> Removed from DISCARD: Yes")
            success_count += 1
        elif found_in_clean and found_in_discard:
            print(f"  [WARNING] {fname} exists in BOTH clean and discard!")
        elif not found_in_clean:
            print(f"  [ERROR] {fname} was NOT found in the clean folder!")
            
    print(f"\nVerification completed: {success_count} of {len(unique_filenames)} files checked successfully.")

if __name__ == "__main__":
    main()
