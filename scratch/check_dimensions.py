import os
from PIL import Image

SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full"
V3_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\artiklar"

bad_images = [
    "010-natural.jpg", "100437.jpg", "100438.jpg", "100514.jpg", "102576.jpg",
    "1211-c.jpg", "15135-1.jpg", "2252-svart.jpg", "2300232.jpg", "45921.jpg",
    "85624.jpg", "88983.jpg", "91467.jpg", "91469.jpg", "91682.jpg", "93161.jpg",
    "alm-3061-t-25.jpg", "ct-175.jpg", "ct-186.jpg", "da-163.jpg", "eilens01-wood.jpg",
    "h000018252.jpg", "jn2005-004.jpg", "ks-01-m-silver.jpg", "ks-01-w-wood.jpg",
    "mobellass-large-gra.jpg", "puntwd01.jpg", "rh1905-13.jpg", "rh1905-14.jpg",
    "rh1905-17.jpg", "rh2012-39.jpg", "rh2012-40.jpg", "rh2012-42.jpg", "rw811.jpg",
    "ws-c1008.jpg", "ws-rt01a.jpg", "yd-g18-w.jpg"
]

print(f"{'Filnamn':<25} | {'Finns i SRC':<12} | {'Storlek i SRC':<15} | {'Storlek i V3':<15}")
print("-" * 75)
for img in bad_images:
    src_path = os.path.join(SRC_DIR, "artiklar", img)
    v3_path = os.path.join(V3_DIR, img)
    
    src_exists = os.path.exists(src_path)
    src_size = "N/A"
    v3_size = "N/A"
    
    if src_exists:
        try:
            with Image.open(src_path) as im:
                src_size = f"{im.size[0]}x{im.size[1]}"
        except Exception:
            src_size = "Error"
            
    if os.path.exists(v3_path):
        try:
            with Image.open(v3_path) as im:
                v3_size = f"{im.size[0]}x{im.size[1]}"
        except Exception:
            v3_size = "Error"
            
    print(f"{img:<25} | {str(src_exists):<12} | {src_size:<15} | {v3_size:<15}")
