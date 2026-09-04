import os

folder_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter_aktiva_del2"
if os.path.exists(folder_path):
    files = os.listdir(folder_path)
    rug_files = [f for f in files if "matta" in f.lower() or f.startswith("2")]
    print(f"Rug files in folder ({len(rug_files)}):")
    for f in sorted(rug_files):
        print(f"  {f}")
else:
    print("Folder does not exist.")
