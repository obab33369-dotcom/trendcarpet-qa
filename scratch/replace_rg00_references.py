import os
import shutil
import stat

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception as e:
        print(f"Error making writable {path}: {e}")

correct_src = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Matta 'Ängelholm' - Grön (RG00)\artiklar\RG00.jpg"
destinations = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\2006_matta-angelholm-gron.jpg",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch1_produkter_aktiva_del1\2006_matta-angelholm-gron.jpg",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch1_produkter_aktiva_del3\2006_matta-angelholm-gron.jpg",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch1_produkter_aktiva_del4\2006_matta-angelholm-gron.jpg"
]

print("--- REPLACING RG00 REFERENCES ---")
if not os.path.exists(correct_src):
    print(f"Error: Source file does not exist: {correct_src}")
else:
    for dest in destinations:
        if os.path.exists(dest):
            make_writable(dest)
            try:
                shutil.copy2(correct_src, dest)
                print(f"SUCCESS: Copied correct image to {dest}")
            except Exception as e:
                print(f"FAILED: Copy to {dest} failed: {e}")
        else:
            print(f"NOTE: Destination path does not exist on disk: {dest}")
