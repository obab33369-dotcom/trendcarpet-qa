with open("reforma-turboflow/vision_auto_corrector.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "status_db" in line and ("in" in line or "get" in line) and not line.strip().startswith("#"):
        print(f"Line {idx+1}: {line.strip()}")
