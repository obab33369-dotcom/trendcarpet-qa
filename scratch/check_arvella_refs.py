import os
import hashlib

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")

def get_hash(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return "ERROR"

def main():
    print("=== Checking Arvella Reference Photos ===")
    for item in os.listdir(CLEAN_ROOT):
        if "arvella" in item.lower() or "velenna" in item.lower():
            folder_path = os.path.join(CLEAN_ROOT, item)
            print(f"\nFolder: {item}")
            for f in os.listdir(folder_path):
                if f.startswith("00_REFERENCE_"):
                    p = os.path.join(folder_path, f)
                    h = get_hash(p)
                    print(f"  Reference File: {f}")
                    print(f"    MD5 Hash: {h}")
                    print(f"    Size: {os.path.getsize(p)} bytes")

if __name__ == "__main__":
    main()
