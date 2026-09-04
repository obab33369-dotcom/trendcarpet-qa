import os
import datetime

tf_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

files_to_check = [
    "rooms_turboflow_batch1.json",
    "rooms_turboflow_batch2.json",
    "rooms_turboflow_full_catalog.json",
    "prompts_only_yesterday.txt",
    "turboflow_ready_yesterday.json",
    "turboflow_ready_full_catalog.json"
]

for f in files_to_check:
    path = os.path.join(tf_dir, f)
    if os.path.exists(path):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        size = os.path.getsize(path)
        print(f"File: {f} | Size: {size} bytes | Mtime: {mtime}")
    else:
        print(f"File {f} does not exist.")
