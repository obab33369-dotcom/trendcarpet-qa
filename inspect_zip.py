import zipfile
import os

zip_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out-pt2.zip"
print("Zip file exists:", os.path.exists(zip_path))
if os.path.exists(zip_path):
    print("Zip file size:", os.path.getsize(zip_path), "bytes")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            namelist = zip_ref.namelist()
            print(f"Total files in zip: {len(namelist)}")
            print("First 20 files:")
            for name in namelist[:20]:
                print("  ", name)
            print("Folders in zip:")
            folders = set()
            for name in namelist:
                parts = name.split('/')
                if len(parts) > 1:
                    folders.add(parts[0])
            print("  ", list(folders))
    except Exception as e:
        print("Error reading zip:", e)
