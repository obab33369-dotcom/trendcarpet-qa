import os
import shutil

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")
ORIG_DIR = os.path.join(WORKSPACE_DIR, "reforma-original-images")

def main():
    print("=== FIXING SAKAI FOLDERS ===")
    
    # 1. Target folders
    old_clean_prime = os.path.join(CLEAN_DIR, "Byrå Prime 6 lådor - Vit ek (2108-white-oak)")
    new_clean_sakai = os.path.join(CLEAN_DIR, "Byrå Sakai - Vit (9965)")
    
    # 2. Check if old folder exists
    if not os.path.exists(old_clean_prime):
        print(f"Old Clean Prime folder not found at: {old_clean_prime}")
        print("Nothing to move. Maybe it was already moved or does not exist.")
    else:
        # Create new Sakai folder
        os.makedirs(new_clean_sakai, exist_ok=True)
        
        # Move files
        moved_count = 0
        for item in os.listdir(old_clean_prime):
            if item.startswith("00_REFERENCE_"):
                continue
            src = os.path.join(old_clean_prime, item)
            dest = os.path.join(new_clean_sakai, item)
            if os.path.isfile(src):
                print(f"Moving {item} to {new_clean_sakai}...")
                shutil.move(src, dest)
                moved_count += 1
                
        print(f"Moved {moved_count} renders to Byrå Sakai - Vit (9965).")
        
        # Copy correct reference photo
        ref_photo_src = os.path.join(ORIG_DIR, "9965.jpg")
        if os.path.exists(ref_photo_src):
            ref_photo_dest = os.path.join(new_clean_sakai, "00_REFERENCE_9965.jpg")
            print(f"Copying reference image 9965.jpg to {ref_photo_dest}...")
            shutil.copy2(ref_photo_src, ref_photo_dest)
        else:
            print("Warning: 9965.jpg not found in reforma-original-images!")
            
        # Clean up old empty Prime folder
        try:
            # check if anything is left
            remaining = os.listdir(old_clean_prime)
            for r in remaining:
                os.remove(os.path.join(old_clean_prime, r))
            os.rmdir(old_clean_prime)
            print(f"Deleted old empty Prime folder: {old_clean_prime}")
        except Exception as e:
            print(f"Could not delete old Prime folder: {e}")
            
    # 3. Clean up Discard Directory for Prime if empty
    old_discard_prime = os.path.join(DISCARD_DIR, "Byrå Prime 6 lådor - Vit ek (2108-white-oak)")
    if os.path.exists(old_discard_prime):
        try:
            remaining = os.listdir(old_discard_prime)
            if not remaining:
                os.rmdir(old_discard_prime)
                print(f"Deleted empty Prime folder in Discard Directory: {old_discard_prime}")
            else:
                print(f"Old Prime Discard folder contains files: {remaining}")
        except Exception as e:
            print(f"Could not delete old Prime Discard folder: {e}")
            
    print("Sakai folder fix complete!")

if __name__ == "__main__":
    main()
