import shutil
import os

src_orig = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Stol 'Pine' - Natur (WS-8652)\artiklar\zoom\WS-8652_1.jpg"
src_fail = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\WS-8652_1.jpg"

dest_orig = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\original_WS-8652_1.jpg"
dest_fail = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\failed_WS-8652_1.jpg"

try:
    if os.path.exists(src_orig):
        shutil.copy(src_orig, dest_orig)
        print("Copied original.")
    else:
        print("Original not found at:", src_orig)
        
    if os.path.exists(src_fail):
        shutil.copy(src_fail, dest_fail)
        print("Copied failed.")
    else:
        print("Failed image not found at:", src_fail)
except Exception as e:
    print("Error:", e)
