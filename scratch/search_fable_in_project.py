import os

scratch_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch"

print("Searching for files with 'fable' in the name:")
for root, dirs, files in os.walk(scratch_dir):
    for f in files:
        if "fable" in f.lower():
            print(f"  {os.path.join(root, f)}")

print("\nSearching for files containing 'fable':")
for root, dirs, files in os.walk(scratch_dir):
    for f in files:
        if f.endswith(('.py', '.txt', '.md', '.json')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as file_obj:
                    content = file_obj.read()
                    if "fable" in content.lower() and "query_fable" not in f:
                        print(f"  {path} (contains 'fable')")
            except Exception:
                pass
