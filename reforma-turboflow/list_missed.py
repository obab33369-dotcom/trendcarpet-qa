import os
path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temporary-ftp-upload\artiklar"
if os.path.exists(path):
    files = os.listdir(path)
    print(f"Total files in {path}: {len(files)}")
    print("Files:")
    for f in files:
        print(f"  {f}")
else:
    print("Path does not exist")
