import os
import hashlib

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
orig_dir = os.path.join(WORKSPACE_DIR, "reforma-original-images")

def get_file_info(filename):
    p = os.path.join(orig_dir, filename)
    if os.path.exists(p):
        size = os.path.getsize(p)
        with open(p, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        return f"Exists | Size: {size} bytes | MD5: {md5}"
    else:
        return "Does not exist"

print("=== CARPET REFERENCES IN ORIG DIR ===")
print(f"RG01-1.jpg (Seronis):   {get_file_info('RG01-1.jpg')}")
print(f"RG01-19.jpg (Aravelle): {get_file_info('RG01-19.jpg')}")
print(f"RG01-49.jpg (Sorvento): {get_file_info('RG01-49.jpg')}")
print(f"RG01-499.jpg (Orlisse): {get_file_info('RG01-499.jpg')}")

# Also check inside OneDrive articles folder
print("\n=== CARPET REFERENCES IN ONEDRIVE FTP DIR ===")
ftp_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload\artiklar"

def get_ftp_info(filename):
    p = os.path.join(ftp_dir, filename)
    if os.path.exists(p):
        size = os.path.getsize(p)
        with open(p, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        return f"Exists | Size: {size} bytes | MD5: {md5}"
    else:
        return "Does not exist"

print(f"RG01-1.jpg (Seronis):   {get_ftp_info('RG01-1.jpg')}")
print(f"RG01-19.jpg (Aravelle): {get_ftp_info('RG01-19.jpg')}")
print(f"RG01-49.jpg (Sorvento): {get_ftp_info('RG01-49.jpg')}")
print(f"RG01-499.jpg (Orlisse): {get_ftp_info('RG01-499.jpg')}")
