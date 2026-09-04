import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

gt_path = os.path.join(WORKSPACE_DIR, "scratch", "gemini_ground_truth.json")
if os.path.exists(gt_path):
    with open(gt_path, 'r', encoding='utf-8') as f:
        gt = json.load(f)
    print(f"Loaded {len(gt)} ground truth records.")
    
    targets = ["1973", "2019", "2041", "2099", "2145"]
    for k, v in gt.items():
        for t in targets:
            if k.startswith(t):
                print(f"File: {k} | Decision: {v}")
else:
    print("gemini_ground_truth.json not found")
