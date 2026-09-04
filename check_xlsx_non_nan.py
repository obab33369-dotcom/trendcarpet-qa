import pandas as pd
path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out\Bade_IK100101936_Foto.xlsx"
df = pd.read_excel(path)
print("Non-null Status counts:")
print(df['Status'].value_counts(dropna=False))
print("\nNon-null Datum Upptänd counts:")
print(df['Datum Upptnd'].value_counts(dropna=False))
print("\nAll rows where Status or Datum is not null:")
print(df[df['Status'].notnull() | df['Datum Upptnd'].notnull()])
