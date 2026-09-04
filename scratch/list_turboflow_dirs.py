import os

base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
if os.path.exists(base_dir):
    print(f"Listing subdirectories in: {base_dir}")
    for item in os.listdir(base_dir):
        full_path = os.path.join(base_dir, item)
        if os.path.isdir(full_path):
            print(f"DIR: {item}")
else:
    print(f"Path does not exist: {base_dir}")
