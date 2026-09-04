import os
import glob
import time

brain_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b"
files = glob.glob(os.path.join(brain_dir, "**", "media*"), recursive=True)

for f in sorted(files):
    mtime = os.path.getmtime(f)
    mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
    print(f"{os.path.relpath(f, brain_dir)}: {os.path.getsize(f)} bytes, modified: {mtime_str}")
