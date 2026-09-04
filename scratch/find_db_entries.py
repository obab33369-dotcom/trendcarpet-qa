import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
DB_DIR = os.path.join(WORKSPACE_DIR, "reforma-turboflow")

def search_index_in_db(idx):
    found = False
    for filename in os.listdir(DB_DIR):
        if filename.endswith(".json"):
            path = os.path.join(DB_DIR, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    continue
                for item in data:
                    prompt = item.get('prompt', '')
                    m = prompt.strip().split('-')[0].strip()
                    if m == str(idx):
                        print(f"Index {idx} found in {filename}:")
                        print(f"  Prompt: {prompt}")
                        print(f"  Refs: {item.get('image_references', '')}")
                        found = True
            except Exception as e:
                pass
    if not found:
        print(f"Index {idx} not found in any database.")

def main():
    for idx in [2087, 2089, 2104, 2113]:
        search_index_in_db(idx)
        print()

if __name__ == "__main__":
    main()
