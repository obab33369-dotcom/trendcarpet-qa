import os
import shutil
import csv
import glob

project_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

# 1. Clean old batch folders
print("Cleaning old batch folders...")
for folder in glob.glob(os.path.join(project_dir, "batch*_images")):
    try:
        shutil.rmtree(folder)
    except:
        pass

# 2. Delete old batch files
print("Cleaning old batch files...")
for file in glob.glob(os.path.join(project_dir, "*_batch*.txt")) + glob.glob(os.path.join(project_dir, "*_batch*.csv")):
    try:
        os.remove(file)
    except:
        pass

csv_file = os.path.join(project_dir, "turboflow_tracking_log_full_catalog.csv")
txt_file = os.path.join(project_dir, "turboflow_ready_full_catalog.txt")
prompt_file = os.path.join(project_dir, "prompts_only_full_catalog.txt")

with open(csv_file, 'r', encoding='utf-8') as f:
    csv_lines = f.readlines()
with open(txt_file, 'r', encoding='utf-8') as f:
    txt_lines = f.readlines()
with open(prompt_file, 'r', encoding='utf-8') as f:
    prompt_lines = f.readlines()

header_csv = csv_lines[0]
data_csv = csv_lines[1:]

IMAGE_LIMIT = 185  # Max 185 unique images per batch to be safe

batches = []
current_batch_csv = []
current_batch_txt = []
current_batch_prompt = []
current_images = set()

for i, row in enumerate(data_csv):
    # Parse the row to see what images it uses
    row_parsed = list(csv.reader([row], delimiter=';'))[0]
    # 'References Utilized' is column 16 (0-indexed)
    refs = row_parsed[16] if len(row_parsed) > 16 else ""
    row_images = set([r.strip() for r in refs.split(';') if r.strip()])
    
    # Check if adding this row exceeds the limit
    future_images = current_images.union(row_images)
    
    if len(future_images) > IMAGE_LIMIT and current_batch_csv:
        # Save current batch
        batches.append({
            'csv': current_batch_csv,
            'txt': current_batch_txt,
            'prompt': current_batch_prompt
        })
        # Start new batch
        current_batch_csv = [row]
        current_batch_txt = [txt_lines[i]]
        current_batch_prompt = [prompt_lines[i]]
        current_images = set(row_images)
    else:
        current_batch_csv.append(row)
        current_batch_txt.append(txt_lines[i])
        current_batch_prompt.append(prompt_lines[i])
        current_images = future_images

if current_batch_csv:
    batches.append({
        'csv': current_batch_csv,
        'txt': current_batch_txt,
        'prompt': current_batch_prompt
    })

print(f"Split into {len(batches)} batches based on image limit of {IMAGE_LIMIT}")

for i, batch in enumerate(batches, 1):
    csv_lines = batch['csv']
    txt_lines = batch['txt']
    prompt_lines = batch['prompt']
    
    # 1. Write the full batch files
    with open(os.path.join(project_dir, f"turboflow_tracking_log_full_catalog_batch{i}.csv"), 'w', encoding='utf-8', newline='') as f:
        f.write(header_csv)
        f.writelines(csv_lines)
        
    with open(os.path.join(project_dir, f"turboflow_ready_full_catalog_batch{i}.txt"), 'w', encoding='utf-8') as f:
        f.writelines(txt_lines)
        
    with open(os.path.join(project_dir, f"prompts_only_full_catalog_batch{i}.txt"), 'w', encoding='utf-8') as f:
        f.writelines(prompt_lines)

    # 2. Write the split sub-batch files
    n = len(csv_lines)
    half = n // 2
    # Align to seed boundary (multiples of 10)
    half = (half // 10) * 10
    if half == 0:
        half = n
        
    sub_batches = [
        ('a', csv_lines[:half], txt_lines[:half], prompt_lines[:half]),
        ('b', csv_lines[half:], txt_lines[half:], prompt_lines[half:])
    ]
    
    for suffix, sub_csv, sub_txt, sub_prompt in sub_batches:
        if not sub_csv:
            continue
            
        with open(os.path.join(project_dir, f"turboflow_tracking_log_full_catalog_batch{i}{suffix}.csv"), 'w', encoding='utf-8', newline='') as f:
            f.write(header_csv)
            f.writelines(sub_csv)
            
        with open(os.path.join(project_dir, f"turboflow_ready_full_catalog_batch{i}{suffix}.txt"), 'w', encoding='utf-8') as f:
            f.writelines(sub_txt)
            
        with open(os.path.join(project_dir, f"prompts_only_full_catalog_batch{i}{suffix}.txt"), 'w', encoding='utf-8') as f:
            f.writelines(sub_prompt)
            
print("Splitting complete! You can now run build_image_folders.py")
