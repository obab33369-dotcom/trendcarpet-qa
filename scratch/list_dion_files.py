import os
folder = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\armchairs\Fåtölj _Dion_ - SammetRosa"
if os.path.exists(folder):
    print(os.listdir(folder))
else:
    print("Folder does not exist")
