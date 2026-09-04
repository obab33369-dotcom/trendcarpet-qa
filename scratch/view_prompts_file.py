import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
prompts_file = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'prompts_only_full_catalog.txt')

if os.path.exists(prompts_file):
    print(f"Found prompts file. First 10 lines:")
    with open(prompts_file, 'r', encoding='utf-8') as f:
        for i in range(10):
            line = f.readline()
            if not line:
                break
            print(f"Line {i+1}: {line.strip()}")
else:
    print("Prompts file not found!")
