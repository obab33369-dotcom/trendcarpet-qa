with open("generate_full_catalog_rooms.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if any(word in line for word in ["autotag", "image_references", "image_tags"]):
        print(f"{idx+1}: {line.strip()}")
