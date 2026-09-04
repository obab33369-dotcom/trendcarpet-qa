import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# Load DBs
def load_db(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

batch1 = load_db("rooms_turboflow_batch1.json")
full_catalog = load_db("rooms_turboflow_full_catalog.json")

# Print first 20 prompts from batch1 to see their numbers
print("--- Batch 1 Prompts ---")
count = 0
for item in batch1:
    prompt = item.get("prompt", "")
    m = re.match(r"^(\d+)\s*-", prompt)
    if m:
        num = int(m.group(1))
        print(f"Index: {num} | Prompt: {prompt[:100]}...")
        count += 1
        if count >= 20:
            break

# Print first 20 prompts from full_catalog to see their numbers
print("\n--- Full Catalog Prompts ---")
count = 0
for item in full_catalog:
    prompt = item.get("prompt", "")
    m = re.match(r"^(\d+)\s*-", prompt)
    if m:
        num = int(m.group(1))
        print(f"Index: {num} | Prompt: {prompt[:100]}...")
        count += 1
        if count >= 20:
            break
