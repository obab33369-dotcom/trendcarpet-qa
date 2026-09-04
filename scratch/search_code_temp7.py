with open("reforma-turboflow/vision_auto_corrector.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "WB_FIX_FOLDERS" in line:
        print(f"Line {idx+1}: {line.strip()}")
