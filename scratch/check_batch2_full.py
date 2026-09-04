import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_text_in_db(filename, term):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        print(f"File not found: {p}")
        return
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n--- Searching for '{term}' in {filename} ---")
    matches = 0
    for idx, item in enumerate(data):
        item_str = json.dumps(item, ensure_ascii=False)
        if term.lower() in item_str.lower():
            matches += 1
            print(f"Match {matches}:")
            print(f"  Prompt: {item.get('prompt', '')[:200]}...")
            print(f"  Refs: {item.get('image_references', '')}")
            if matches >= 5:
                print("Showing first 5 matches only.")
                break
    if matches == 0:
        print("No matches found.")

def main():
    search_text_in_db("rooms_turboflow_batch2.json", "1558")
    search_text_in_db("rooms_turboflow_batch2.json", "1688")
    search_text_in_db("rooms_turboflow_batch2.json", "väddö")
    search_text_in_db("rooms_turboflow_batch2.json", "vadd")

if __name__ == "__main__":
    main()
