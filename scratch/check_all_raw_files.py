import os

INPUT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images"
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

print(f"{'Filnamn':<25} | {'Rå original i INPUT_DIR':<25}")
print("-" * 60)
for img in bad_images:
    raw_path = os.path.join(INPUT_DIR, "artiklar", img)
    # also try sku extracted
    sku = os.path.splitext(img)[0]
    raw_path_sku = os.path.join(INPUT_DIR, "artiklar", f"{sku}.jpg")
    
    exists = os.path.exists(raw_path) or os.path.exists(raw_path_sku)
    print(f"{img:<25} | {str(exists):<25}")
