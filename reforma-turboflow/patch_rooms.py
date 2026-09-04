import re

PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\generate_batch2_rooms.py"

with open(PATH, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Remove the first duplicate definition of get_dynamic_location that is placed right after join_background_elements
duplicate_pattern = r"def join_background_elements\(elements: List\[str\], close_up: bool\) -> str:.*?(\n    def get_dynamic_location\(pkg_idx: int, is_kitchen: bool\) -> Tuple\[str, str\]:.*?return desc, name\n)"
# Let's inspect the code to find the first definition:
first_def_start = code.find("def join_background_elements(elements: List[str], close_up: bool) -> str:")
second_def_start = code.find("def get_dynamic_location(pkg_idx: int, is_kitchen: bool) -> Tuple[str, str]:", first_def_start + 1)
# Let's cut the duplicate definition out
# The first definition is between first_def_start and second_def_start
# Let's find the closing return statement of that first get_dynamic_location:
first_get_location_start = code.find("def get_dynamic_location(pkg_idx: int, is_kitchen: bool) -> Tuple[str, str]:")
first_return = code.find("return desc, name", first_get_location_start)
first_def_end = first_return + len("return desc, name\n")

duplicate_part = code[first_get_location_start:first_def_end]
print(f"Duplicate part length: {len(duplicate_part)}")

# Clean duplicate definition
code_cleaned = code[:first_get_location_start] + code[first_def_end:]

# 2. Locate the real definition of get_dynamic_location inside main()
# Now there is only one get_dynamic_location definition remaining in code_cleaned!
real_start = code_cleaned.find("def get_dynamic_location(pkg_idx: int, is_kitchen: bool) -> Tuple[str, str]:")
real_return = code_cleaned.find("return desc, name", real_start)
real_end = real_return + len("return desc, name\n")

real_original = code_cleaned[real_start:real_end]

real_replacement = """def get_dynamic_location(pkg_idx: int, is_kitchen: bool) -> Tuple[str, str]:
        \"\"\"
        Returns (room_and_setting_desc, location_name) for the package.
        The 6 environments are:
        1. Stockholm classic turn-of-the-century apartment in Östermalm
        2. Scandi kitchen-living room / Scandi living room
        3. Stockholm archipelago architect-designed villa
        4. Scandi architect-designed cabin
        5. Scandi architect-designed living room with garden
        6. Scandi penthouse
        \"\"\"
        env_type = pkg_idx % 6
        
        if env_type == 0:
            room = "kitchen-living room" if is_kitchen else "living room"
            fireplace = "a classic tiled stove (kakelugn) in the corner" if (pkg_idx % 2 == 0) else "a clean empty fireplace against the wall"
            desc = f"Stockholm classic turn-of-the-century apartment {room} in Östermalm with {fireplace}, and views of tree-lined streets"
            name = "Classic Stockholm Apartment"
        elif env_type == 1:
            room = "Scandi kitchen-living room" if is_kitchen else "Scandi living room"
            desc = f"{room} with large windows, soft plaster walls, and light-toned ash floors"
            name = "Scandi Apartment"
        elif env_type == 2:
            room = "kitchen-living room" if is_kitchen else "living room"
            desc = f"Stockholm archipelago architect-designed villa {room} with massive floor-to-ceiling glass walls looking out over a serene waterfront and rocky pine shores"
            name = "Stockholm Archipelago Villa"
        elif env_type == 3:
            room = "kitchen-living room" if is_kitchen else "living room"
            desc = f"Scandi architect-designed cabin {room} featuring exposed pine timber structures and large windows facing a misty forest landscape"
            name = "Scandi Architect Cabin"
        elif env_type == 4:
            room = "kitchen-living room with garden view" if is_kitchen else "living room with garden view"
            desc = f"Scandi architect-designed {room}, set against large glass doors looking out onto a modern courtyard garden"
            name = "Scandi Villa with Garden"
        else: # env_type == 5
            room = "kitchen-living room" if is_kitchen else "living room"
            desc = f"Scandi penthouse {room} with panoramic windows, high ceilings, and sweeping views of city rooftops"
            name = "Scandi Penthouse"
            
        return desc, name"""

# Make sure replacement has the same indentations
indented_replacement = "\n".join("    " + line for line in real_replacement.split("\n"))

code_final = code_cleaned[:real_start] + indented_replacement + code_cleaned[real_end:]

with open(PATH, "w", encoding="utf-8") as f:
    f.write(code_final)

print("Real get_dynamic_location successfully replaced and duplicate removed!")
