import os
import datetime

filepath = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\2019-architectural-digest-styl-229.png"
if os.path.exists(filepath):
    mtime = os.path.getmtime(filepath)
    dt = datetime.datetime.fromtimestamp(mtime)
    print(f"File: {filepath}")
    print(f"Modified: {dt}")
else:
    print("File does not exist")
