import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

report_path = os.path.join(WORKSPACE_DIR, "scratch", "empty_folders_classification.json")
if os.path.exists(report_path):
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    targets = [
        "1973-architectural-digest-styl-183.png", 
        "2019-architectural-digest-styl-229.png", 
        "2041-architectural-digest-styl-251.png", 
        "2099-architectural-digest-styl-309.png",
        "2145-architectural-digest-styl-032.png"
    ]
    
    for t in targets:
        if t in report:
            print(f"\n=== File: {t} ===")
            print(json.dumps(report[t], indent=2, ensure_ascii=False))
        else:
            # Try fuzzy match
            found = False
            for k, v in report.items():
                if t.lower() in k.lower():
                    print(f"\n=== File: {k} ===")
                    print(json.dumps(v, indent=2, ensure_ascii=False))
                    found = True
                    break
            if not found:
                print(f"File: {t} NOT found in report")
else:
    print("empty_folders_classification.json not found")
