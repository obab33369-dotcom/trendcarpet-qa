import os
import datetime

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

files = [
    "generate_full_catalog_rooms.py",
    "turboflow_ready_full_catalog.txt",
    "prompts_only_full_catalog.txt",
    "turboflow_tracking_log_full_catalog.csv",
    "prompts_only_full_catalog_batch2b.txt",
    "turboflow_tracking_log_full_catalog_batch2b.csv"
]

for f in files:
    path = os.path.join(project_dir, f)
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        dt = datetime.datetime.fromtimestamp(mtime)
        print(f"File: {f} -> Last Modified: {dt}")
    else:
        print(f"File: {f} -> Not Found")
