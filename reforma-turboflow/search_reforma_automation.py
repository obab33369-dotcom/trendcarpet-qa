import os

path = r"C:\Users\AndronikLindgren\reforma_automation"
if os.path.exists(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            if "portofino" in f.lower() or "t8049" in f.lower():
                print(f"FOUND: {os.path.join(root, f)}")
else:
    print("Path does not exist")
