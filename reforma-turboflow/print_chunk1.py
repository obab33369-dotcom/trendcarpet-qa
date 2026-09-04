import os

filepath = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\prompts_chunk_1.txt"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(min(len(lines), 30)):
    print(f"Line {idx+1}: {lines[idx].strip()}")
