from PIL import Image
import os

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\Rio-1-rigth-Grace01_10.jpg"

if os.path.exists(img_path):
    with Image.open(img_path) as img:
        print(f"File: {os.path.basename(img_path)}")
        print(f"Dimensions: {img.size}")
else:
    print(f"File not found: {img_path}")
