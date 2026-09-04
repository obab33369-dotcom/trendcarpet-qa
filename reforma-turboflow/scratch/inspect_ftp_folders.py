import os

base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-18-FTP"
folder1 = os.path.join(base_dir, "Inte-dessa-Uppdaterade-på-sajt-undersök-FTP", "artiklar")
folder2 = os.path.join(base_dir, "artiklar")

print("FOLDER 1 (recursed) EXISTS:", os.path.exists(folder1))
if os.path.exists(folder1):
    contents = os.listdir(folder1)
    print(f"Folder 1 contents count: {len(contents)}")
    print("Some contents:")
    for c in contents[:15]:
        print(" -", c)

print("\nFOLDER 2 EXISTS:", os.path.exists(folder2))
if os.path.exists(folder2):
    contents = os.listdir(folder2)
    print(f"Folder 2 contents count: {len(contents)}")
    print("Some contents:")
    for c in contents[:15]:
        print(" -", c)
