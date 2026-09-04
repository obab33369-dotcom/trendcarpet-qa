import os

turboflow_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
print("Turboflow dir contents:")
if os.path.exists(turboflow_dir):
    try:
        for f in os.listdir(turboflow_dir):
            p = os.path.join(turboflow_dir, f)
            if os.path.isdir(p):
                print(f"  [Folder] {f}")
            else:
                print(f"  [File] {f} - {os.path.getsize(p)} bytes")
    except Exception as e:
        print("Error listing dir:", e)
else:
    print("Turboflow dir does not exist.")
