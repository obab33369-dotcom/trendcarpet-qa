import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def check_db(filename, indices):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        print(f"File not found: {p}")
        return
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n--- Checking {filename} ---")
    for item in data:
        prompt = item.get('prompt', '')
        # Check if the prompt starts with one of our indices
        for idx in indices:
            if prompt.strip().startswith(f"{idx}-") or prompt.strip().startswith(f"{idx} -"):
                print(f"Index {idx}:")
                print(f"  Prompt: {prompt}")
                print(f"  Refs: {item.get('image_references', '')}")

def main():
    indices = [1558, 1688]
    check_db("rooms_turboflow_batch1.json", indices)
    check_db("rooms_turboflow_batch2.json", indices)
    check_db("rooms_turboflow_full_catalog.json", indices)

if __name__ == "__main__":
    main()
