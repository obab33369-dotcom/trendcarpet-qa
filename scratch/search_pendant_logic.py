import os

search_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
print("Searching for lamp_pendant/pendant/taklampa in python files...")

for root, dirs, files in os.walk(search_dir):
    for f in files:
        if f.endswith('.py') and not f.startswith('tmp'):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if 'lamp_pendant' in content or 'taklampa' in content:
                        print(f"File: {p}")
                        for idx, line in enumerate(content.splitlines(), 1):
                            if 'lamp_pendant' in line or 'taklampa' in line or 'pendant' in line:
                                print(f"  Line {idx}: {line.strip()[:100]}")
            except Exception as e:
                pass
