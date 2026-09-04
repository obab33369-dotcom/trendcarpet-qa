import os

v3_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\artiklar"
if os.path.exists(v3_dir):
    files = [f for f in os.listdir(v3_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    print(f"Hittade {len(files)} bilder i {v3_dir}")
    print("De första 20 filerna:")
    for f in files[:20]:
        print(" -", f)
else:
    print(f"Katalogen {v3_dir} finns inte.")
