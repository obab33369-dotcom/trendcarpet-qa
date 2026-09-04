filepath = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\vision_auto_corrector.py"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching for 'narrow_categories' in vision_auto_corrector.py ---")
for idx, line in enumerate(lines):
    if "narrow_categories" in line:
        # Avoid print encoding issues in windows by replacing special chars
        safe_line = line.strip().encode('ascii', errors='replace').decode('ascii')
        print(f"Line {idx+1}: {safe_line}")
