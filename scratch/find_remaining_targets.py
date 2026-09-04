import os
import sys

file_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\vision_auto_corrector.py"
out_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\remaining_targets.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []

def find_and_record(pattern, count=10):
    output.append(f"\n=== PATTERN: {pattern} ===")
    for idx, line in enumerate(lines):
        if pattern in line:
            start = max(0, idx - 2)
            end = min(len(lines), idx + count)
            for j in range(start, end):
                output.append(f"{j+1}: {lines[j]}")

find_and_record("def process_single_main_image")
find_and_record("is_ok = (0.95 <= scale_needed")
find_and_record("def process_single_zoom_image")
find_and_record("db_key = f\"zoom/{f}\"")
find_and_record("limit = None")
find_and_record("unreviewed_main = []")
find_and_record("unreviewed_zoom = []")
find_and_record("process_single_main_image(f")
find_and_record("process_single_zoom_image(f")

with open(out_path, 'w', encoding='utf-8') as f_out:
    f_out.writelines(output)

print("Targets recorded successfully in scratch/remaining_targets.txt")
