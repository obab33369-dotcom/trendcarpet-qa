import os

TARGET_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-ny-sortering\Baddsoffa Texas Ljusgra (MLM-502580-lightgrey)"

if os.path.exists(TARGET_DIR):
    print("=== Main Folder ===")
    main_files = [f for f in os.listdir(TARGET_DIR) if os.path.isfile(os.path.join(TARGET_DIR, f))]
    print(f"Total main files: {len(main_files)}")
    for f in sorted(main_files):
        print(f"  - {f}")
        
    reserv_dir = os.path.join(TARGET_DIR, "reserv")
    if os.path.exists(reserv_dir):
        print("\n=== Reserv Folder ===")
        reserv_files = os.listdir(reserv_dir)
        print(f"Total reserv files: {len(reserv_files)}")
        for f in sorted(reserv_files):
            print(f"  - {f}")
else:
    print("Texas target folder not found!")
