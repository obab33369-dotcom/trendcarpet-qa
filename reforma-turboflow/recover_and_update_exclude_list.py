import os
import re
import json

turboflow_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
master_json_path = "turboflow_ready_yesterday.json"
exclude_list_path = "exclude_list.json"

# 1. Scan turboflow dir for generated Ns
generated_indices = set()
for filename in os.listdir(turboflow_dir):
    if filename.endswith(".png"):
        m = re.match(r"^(\d+)-architectural", filename)
        if m:
            n = int(m.group(1))
            generated_indices.add(n - 1)  # 0-based index

print(f"Found {len(generated_indices)} generated images.")

# 2. Load the master JSON
with open(master_json_path, 'r', encoding='utf-8') as f:
    master_db = json.load(f)

# 3. Extract the primary furniture ID for each generated index
new_excludes = set()
for idx in generated_indices:
    if idx < len(master_db):
        row = master_db[idx]
        refs = row.get("image_references", "")
        # The primary furniture is the first reference
        first_ref = refs.split(";")[0].strip()
        if first_ref:
            new_excludes.add(first_ref)

print(f"Found {len(new_excludes)} unique primary furniture items to exclude.")

# 4. Update exclude_list.json
if os.path.exists(exclude_list_path):
    with open(exclude_list_path, 'r', encoding='utf-8') as f:
        exclude_list = set(json.load(f))
else:
    exclude_list = set()

initial_count = len(exclude_list)
exclude_list.update(new_excludes)
final_count = len(exclude_list)

print(f"Added {final_count - initial_count} new items to exclude_list.json.")

with open(exclude_list_path, 'w', encoding='utf-8') as f:
    json.dump(list(exclude_list), f, indent=4, ensure_ascii=False)

print("Done! exclude_list.json has been updated.")
