import os
from PIL import Image

path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\3944_chair-lionel-beige-1-26U-wonder.webp"
img = Image.open(path)
print("Image size:", img.size)
