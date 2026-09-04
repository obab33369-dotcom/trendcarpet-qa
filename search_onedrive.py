import os
dir_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
results = []
for name in os.listdir(dir_path):
    if "26-06-05" in name:
        results.append(name)
print("Found items with '26-06-05':", results)
