import os
import json

LOG_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\9a89adb6-c2a2-4ca2-a186-3ca3c4d5681e\.system_generated\tasks\task-6327.log"
STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\review_status.json"

skus_to_check = [
    "1091-black", "1091-walnut", "6027-natur", "6027-walnut", 
    "rw811", "99070", "throw-striped-12", "dc-070", "rio-1-fortis01", "ellewd02-black"
]

status_db = {}
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = {k.lower(): v for k, v in json.load(f).items()}

out_lines = []
out_lines.append("--- DB Status ---")
for sku in skus_to_check:
    db_keys = [k for k in status_db.keys() if sku in k]
    for k in db_keys:
        out_lines.append(f"Key: {k} -> Status: {status_db[k].get('status')} | Reason: {status_db[k].get('reason')}")

out_lines.append("\n--- Log Grep ---")
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for sku in skus_to_check:
        out_lines.append(f"\n--- Log for {sku} ---")
        found = False
        for i, line in enumerate(lines):
            if sku in line.lower() or sku.replace('-', '') in line.lower():
                start = max(0, i - 1)
                end = min(len(lines), i + 6)
                for j in range(start, end):
                    out_lines.append(f"  {j+1}: {lines[j].strip()}")
                out_lines.append("  ...")
                found = True
        if not found:
            out_lines.append("  Not found in log.")

with open(r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\specific_skus_status.txt", 'w', encoding='utf-8') as f_out:
    f_out.write("\n".join(out_lines))
print("Wrote output to specific_skus_status.txt")
