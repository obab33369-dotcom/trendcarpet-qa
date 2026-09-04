import os
import hashlib

def file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2 - Originals Backup"
    
    pairs = [
        ("HPEJ9251.JPG", "OMFT5250.JPG"),
        ("NTHT9785.JPG", "RXSA5233.JPG")
    ]
    
    for f1, f2 in pairs:
        p1 = os.path.join(src_dir, f1)
        p2 = os.path.join(src_dir, f2)
        if os.path.exists(p1) and os.path.exists(p2):
            hash1 = file_hash(p1)
            hash2 = file_hash(p2)
            sz1 = os.path.getsize(p1)
            sz2 = os.path.getsize(p2)
            print(f"\nComparing {f1} and {f2}:")
            print(f"  - {f1}: size={sz1} bytes, hash={hash1[:16]}...")
            print(f"  - {f2}: size={sz2} bytes, hash={hash2[:16]}...")
            if hash1 == hash2:
                print("  - RESULT: THEY ARE IDENTICAL FILES!")
            else:
                print("  - RESULT: They are different files (different photos).")
        else:
            print(f"Files not found: {f1} or {f2}")

if __name__ == "__main__":
    main()
