import os

file_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\vision_auto_corrector.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_around(pattern, count=5):
    print(f"\n=== PATTERN: {pattern} ===")
    for idx, line in enumerate(lines):
        if pattern in line:
            start = max(0, idx - 2)
            end = min(len(lines), idx + count)
            for j in range(start, end):
                print(f"{j+1}: {lines[j]}", end="")

print_around("def find_original_source_image")
print_around("TEST TOPAZ (disabled")
print_around("def process_single_main_image")
print_around("db_key = f\"artiklar/{f}\"")
print_around("is_closeup = False", count=10)
print_around("def process_single_zoom_image")
print_around("db_key = f\"zoom/{f}\"")
print_around("limit = None")
print_around("unreviewed_main = []")
print_around("unreviewed_zoom = []")
print_around("process_single_main_image(f")
print_around("process_single_zoom_image(f")
