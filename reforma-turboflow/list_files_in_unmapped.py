import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

NEW_WHITE_BG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"
unmapped_dirs = [
    r"Refoma chair\21 Stol _Montmartre_ - Vintage svart (ảnh web)",
    r"Refoma chair\28 Stol _Montmartre_ - Vintage svart_antik (ảnh web)",
    r"Refoma chair\44 Stol _Montmartre_ - Vintage Koppar (ảnh web)",
    r"Refoma chair\49 Stol _Montmartre_ - Vit lackad",
    r"Refoma chair\52 Stol _Montmartre_ - Röd lackad (ảnh web)",
    r"Refoma chair\54 Stol _Montmartre_ - Rustik stål (ảnh web)",
    r"Refoma chair\55 Stol _Montmartre_ - Gul lackad (ảnh web)",
    r"Refoma chair\59 Stol _Montmartre_ - Svart lack (ảnh web)",
    r"Refoma chair\60 Stol _Montmartre_ - Orange lack (ảnh web)"
]

def clean_for_print(s):
    return s.encode('ascii', errors='replace').decode('ascii')

print("--- FILES IN UNMAPPED MONTMARTRE FOLDERS ---")
for ud in unmapped_dirs:
    full_path = os.path.join(NEW_WHITE_BG_DIR, ud)
    print(f"\nFolder: {clean_for_print(ud)}")
    if os.path.exists(full_path):
        files = os.listdir(full_path)
        for f in files[:5]:
            print(f"  {clean_for_print(f)}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more files")
    else:
        print("  Folder does not exist!")
