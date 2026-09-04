with open("generate_batch2_rooms.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "image_references" in line or "files_str" in line or "get_short_filename" in line:
        print(f"{idx+1}: {line.strip()}")
