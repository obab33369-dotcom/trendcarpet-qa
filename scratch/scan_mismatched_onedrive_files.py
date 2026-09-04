import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")

checks = [
    ("Sängbord Elle", "2014-"),
    ("Sidobord/sängbord Sapri", "2023-"),
    ("Barstol Tärnsjö", "2040-"),
    ("Soffbord inkl. tidningsställ Ylva", "2047-"),
    ("Matbord Örsjö Runt 105cm - Natur", "2053-"),
    ("Matbord Örsjö Runt 105cm - Natur", "2083-"),
    ("Sidobord Moliden - Natur", "2100-"),
    ("Skrivbord Neptun - Vit", "2107-"),
    ("Sängbord Detroit - Valnöt/Svart", "2093-")
]

print("=== CHECKING ONEDRIVE FOR MISCLASSIFIED CARPET RENDERS ===")
for folder_sub, prefix in checks:
    # Find folder in TARGET_DIR containing folder_sub
    found = False
    for item in os.listdir(TARGET_DIR):
        if folder_sub.lower() in item.lower():
            path = os.path.join(TARGET_DIR, item)
            reserv_path = os.path.join(path, "reserv")
            if os.path.exists(reserv_path):
                matching_files = [f for f in os.listdir(reserv_path) if f.startswith(prefix)]
                if matching_files:
                    print(f"Folder: {item}")
                    print(f"  Found misclassified files starting with '{prefix}': {matching_files}")
                    found = True
    if not found:
         print(f"No files matching '{prefix}' found under folders matching '{folder_sub}'")
