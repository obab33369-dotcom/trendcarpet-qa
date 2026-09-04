import os

pics_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
print("Scanning OneDrive pictures directory...")
if os.path.exists(pics_dir):
    try:
        for root, dirs, files in os.walk(pics_dir):
            # limit depth to 2
            depth = root[len(pics_dir):].count(os.sep)
            if depth > 2:
                continue
            for f in files:
                if f.lower().endswith(('.xlsx', '.xls', '.csv', '.txt')) and any(kw in f.lower() for kw in ["batch", "ready", "turboflow", "reforma", "foto"]):
                    print(f"  File: {os.path.join(root, f)} | Size: {os.path.getsize(os.path.join(root, f))} bytes")
    except Exception as e:
        print("Error:", e)
else:
    print("Pictures dir does not exist.")
