import os
import datetime

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")

def main():
    if not os.path.exists(CLEAN_DIR):
        print("Clean directory does not exist.")
        return
        
    print("=== SEARCHING FOR FILES APPROVED TODAY ===")
    today = datetime.date.today()
    print(f"Target date: {today}\n")
    
    today_files = []
    
    for root, dirs, files in os.walk(CLEAN_DIR):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                path = os.path.join(root, f)
                # Get modification time
                mtime = os.path.getmtime(path)
                mdate = datetime.date.fromtimestamp(mtime)
                
                # Check if it was modified today
                if mdate == today:
                    today_files.append((f, path, datetime.datetime.fromtimestamp(mtime)))
                    
    print(f"Found {len(today_files)} files moved/approved today ({today}).")
    
    if today_files:
        # Sort by modification time desc
        today_files.sort(key=lambda x: x[2], reverse=True)
        print("\nLast 15 files approved today:")
        for name, path, time in today_files[:15]:
            rel_path = os.path.relpath(path, CLEAN_DIR)
            print(f"  - {time.strftime('%H:%M:%S')} | {rel_path}")
    else:
        print("No files found modified today. (Checking if OneDrive preserves modification time from source file).")
        # OneDrive sometimes preserves the original file modification time instead of the move time.
        # Let's check files in CLEAN_DIR that have a creation time or let's look at the server logs.

if __name__ == "__main__":
    main()
