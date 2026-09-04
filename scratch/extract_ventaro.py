import os

trace_path = r"scratch/carpet_trace.txt"
output_path = r"scratch/ventaro_debug.txt"

with open(trace_path, "r", encoding="cp1252") as f:
    lines = f.readlines()

extracted = []
recording = False
count = 0

for line in lines:
    if "FOLDER: Matta Ventaro" in line:
        recording = True
        count = 0
    elif line.startswith("="*80) and recording and count > 5:
        recording = False
    
    if recording:
        extracted.append(line)
        count += 1

with open(output_path, "w", encoding="utf-8") as f:
    f.writelines(extracted)

print(f"Extracted {len(extracted)} lines to {output_path}")
