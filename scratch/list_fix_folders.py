import os

fix_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"
if os.path.exists(fix_dir):
    print("Folders in Fix Directory:")
    for d in sorted(os.listdir(fix_dir)):
        if os.path.isdir(os.path.join(fix_dir, d)):
            print("  ", d)
else:
    print("Fix directory not found")
