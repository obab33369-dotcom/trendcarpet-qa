file_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\vision_auto_corrector.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Searching for 'def call_gemini_verification':")
for i, line in enumerate(lines):
    if "def call_gemini_verification" in line:
        print(f"Def at line {i+1}: {line.strip()}")
        # print the next 60 lines
        for j in range(i+1, min(i+100, len(lines))):
            print(f"{j+1}: {lines[j].strip()}")
        break
