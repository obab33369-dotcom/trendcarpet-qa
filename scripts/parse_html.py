import re

file_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\interior-designer-automation\templates\index.html"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "geminiApiKey" in line or "aiCurate" in line or "curate" in line:
        print(f"Line {idx+1}: {line.strip()}")
