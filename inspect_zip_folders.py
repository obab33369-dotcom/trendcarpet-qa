import zipfile
import os

zip_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out-pt2.zip"
if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        namelist = zip_ref.namelist()
        
        orig_folders = set()
        px1500_folders = set()
        iphone_folders = set()
        
        for name in namelist:
            parts = name.split('/')
            # e.g., 26-06-05-in-out/Original/Inomhusutomhus-matta-Dhamar-grön/
            if len(parts) >= 4:
                top_folder = parts[1]
                sub_folder = parts[2]
                if top_folder == "Original":
                    orig_folders.add(sub_folder)
                elif top_folder == "1500px":
                    px1500_folders.add(sub_folder)
                elif top_folder == "1500px iphone":
                    iphone_folders.add(sub_folder)
                    
        print("Folders in zip under Original:")
        for f in sorted(list(orig_folders)):
            print("  ", f)
            
        print("\nFolders in zip under 1500px:")
        for f in sorted(list(px1500_folders)):
            print("  ", f)
            
        print("\nFolders in zip under 1500px iphone:")
        for f in sorted(list(iphone_folders)):
            print("  ", f)
