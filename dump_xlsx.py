import pandas as pd
path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out\Bade_IK100101936_Foto.xlsx"
df = pd.read_excel(path)
print(df.to_string())
