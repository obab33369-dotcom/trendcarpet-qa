import os
import glob

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
for txt_file in glob.glob(os.path.join(project_dir, "prompts_only_full_catalog_batch*.txt")):
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        print(f"{os.path.basename(txt_file)}: {len(lines)} prompts")
        
print()
for txt_file in glob.glob(os.path.join(project_dir, "turboflow_ready_full_catalog_batch*.txt")):
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        print(f"{os.path.basename(txt_file)}: {len(lines)} prompts")
