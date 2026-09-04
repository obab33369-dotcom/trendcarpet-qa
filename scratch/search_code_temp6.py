with open("reforma-turboflow/vision_auto_corrector.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def find_original_source_image" in line:
        print(f"Line {idx+1}: {line.strip()}")
        # print the next 50 lines
        for j in range(idx+1, idx+60):
            print(f"Line {j+1}: {lines[j].strip()}")
        break
