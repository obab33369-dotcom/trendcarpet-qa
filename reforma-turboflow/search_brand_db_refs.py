import os

search_word = "brand_sku_dict"
files_to_check = [
    "generate_full_catalog_rooms.py",
    "generate_batch1_rooms.py",
    "generate_batch2_rooms.py",
    "engine.py"
]

for f in files_to_check:
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as f_in:
            content = f_in.read()
        if search_word in content:
            print(f"{f} contains '{search_word}'")
        else:
            print(f"{f} does NOT contain '{search_word}'")
