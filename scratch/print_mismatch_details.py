import json
import os

report_path = r"scratch/carpet_mismatch_report.json"
if os.path.exists(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded mismatch report with {len(data)} folders.")
    for folder, desc in data.items():
        print("="*60)
        print(f"Folder: {folder}")
        print(f"Description: {desc}")
else:
    print("Report path not found")
