import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
plan_path = os.path.join(WORKSPACE_DIR, "scratch", "carpet_redirection_plan.json")

if os.path.exists(plan_path):
    with open(plan_path, "r", encoding="utf-8") as f:
        redirections = json.load(f)
    print(f"Loaded {len(redirections)} folders from carpet_redirection_plan.json.")
    
    print("\nScanning for redirections matching key products:")
    for folder, files in redirections.items():
        # Check if the folder relates to Aureline, Carrano, etc.
        folder_lower = folder.lower()
        if any(keyword in folder_lower for keyword in ["aureline", "carrano", "avendo", "belden", "calvera"]):
            print(f"Folder: {folder}")
            for fn, info in files.items():
                print(f"  File: {fn}")
                print(f"    Matched SKU: {info.get('matched_sku')}")
                print(f"    Matched Name: {info.get('matched_name')}")
                print(f"    Explanation: {info.get('explanation')}")
else:
    print(f"Plan file not found: {plan_path}")
