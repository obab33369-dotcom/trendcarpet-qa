import os

PROJECT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# Search in workspace and OneDrive
search_dirs = [
    WORKSPACE_DIR,
    os.path.join(WORKSPACE_DIR, "reforma-original-images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow"),
    PROJECT_DIR
]

for sd in search_dirs:
    if not os.path.exists(sd):
        continue
    for root, dirs, files in os.walk(sd):
        for f in files:
            if "1397_" in f or "0108_" in f:
                print(os.path.join(root, f))
