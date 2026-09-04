import json
import os
import re
import sys
import subprocess

REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
STATUS_FILE = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\review_status.json"
FAILURES_FILE = os.path.join(REFORMA_DIR, "verification_failures.json")

def main():
    if not os.path.exists(FAILURES_FILE):
        print(f"[ERROR] Failures file not found at {FAILURES_FILE}")
        return
        
    with open(FAILURES_FILE, 'r', encoding='utf-8') as f:
        failures = json.load(f)
        
    print(f"Loaded {len(failures)} failures from {FAILURES_FILE}")
    
    if not os.path.exists(STATUS_FILE):
        print(f"[ERROR] Status file not found at {STATUS_FILE}")
        return
        
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = json.load(f)
        
    # Reset status for failures
    reset_count = 0
    skus = set()
    for path in failures:
        # Key in DB is exactly the path (e.g., "zoom/2108-oak_7.jpg")
        if path in status_db:
            del status_db[path]
            reset_count += 1
            
        # Extract SKU
        filename = os.path.basename(path)
        if path.startswith("zoom/"):
            m = re.match(r"^(.+?)_\d+\.jpg$", filename)
            if m:
                skus.add(m.group(1).lower())
        else:
            skus.add(filename[:-4].lower())
            
    print(f"Reset {reset_count} keys in review_status.json")
    print(f"Extracted {len(skus)} unique SKUs to re-process: {sorted(list(skus))}")
    
    # Save the status DB
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_db, f, indent=2)
    print("Saved review_status.json")
    
    # Run vision_auto_corrector.py with filtered SKUs
    skus_str = ",".join(list(skus))
    cmd = ["python", "vision_auto_corrector.py", f"--skus={skus_str}"]
    print(f"Executing: {' '.join(cmd)}")
    
    # We will run it in the current process to see outputs directly
    sys.argv = ["vision_auto_corrector.py", f"--skus={skus_str}"]
    import vision_auto_corrector
    vision_auto_corrector.main()

if __name__ == "__main__":
    main()
