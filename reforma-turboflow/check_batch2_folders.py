import os

folders = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter_aktiva_del1",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter_aktiva_del2",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch1_produkter_aktiva_del1",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch1_produkter_aktiva_del2"
]

for f in folders:
    if os.path.exists(f):
        print(f"Folder: {f} has {len(os.listdir(f))} files.")
        print("  First 5 files:")
        for fname in os.listdir(f)[:5]:
            print(f"    {fname}")
    else:
        print(f"Folder: {f} does not exist.")
