import os
import datetime

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    dirs = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    found = []
    for d in dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.startswith("421") or f.startswith("422") or f.startswith("075") or f.startswith("076"):
                    path = os.path.join(d, f)
                    if os.path.isfile(path):
                        stat = os.stat(path)
                        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                        found.append((f, mtime, path))
                        
    found.sort(key=lambda x: x[1])
    print("Found files:")
    for f, mtime, path in found:
        print(f"  {f} - Modified: {mtime} - Path: {os.path.basename(os.path.dirname(path))}")

if __name__ == "__main__":
    main()
