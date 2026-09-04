import os

base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-18-FTP"
folder1 = os.path.join(base_dir, "Inte-dessa-Uppdaterade-på-sajt-undersök-FTP", "artiklar")
folder2 = os.path.join(base_dir, "artiklar")

ftp_files = []
if os.path.exists(folder1):
    ftp_files.extend(os.listdir(folder1))
if os.path.exists(folder2):
    ftp_files.extend(os.listdir(folder2))

target_skus = ["37281105", "98875", "1200180", "99684", "91472"]
print("Target SKUs in FTP folders:")
for sku in target_skus:
    found = [f for f in ftp_files if sku.lower() in f.lower()]
    print(f" - {sku}: {found}")
