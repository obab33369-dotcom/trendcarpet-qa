import pandas as pd
path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out\Bade_IK100101936_Foto.xlsx"
df = pd.read_excel(path)
for col in df.columns:
    non_null = df[col].dropna()
    print(f"Col '{col}': {len(non_null)} non-null values")
    if col in ['Status', 'Datum Upptänd'] and len(non_null) > 0:
        print(non_null)
