import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_log(filepath, filename_part):
    results = []
    if not os.path.exists(filepath):
        return results
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline().strip().split(';')
        for idx, line in enumerate(f):
            if filename_part.lower() in line.lower():
                parts = line.strip().split(';')
                results.append((idx + 2, line.strip()))
    return results

log_files = [
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "turboflow_tracking_log.csv"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "turboflow_tracking_log_yesterday.csv"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "turboflow_tracking_log_full_catalog.csv")
]

targets = [
    "017-architectural-digest-style-017",
    "023-architectural-digest-style-023",
    "033-architectural-digest-style-033",
    "637-architectural-digest-style-044",
    "1845-architectural-digest-styl-063"
]

for log_path in log_files:
    print(f"\n================ SEARCHING IN {os.path.basename(log_path)} ================")
    for target in targets:
        matches = search_log(log_path, target)
        if matches:
            print(f"Target: {target} (found {len(matches)} matches):")
            for line_no, content in matches[:3]:
                print(f"  Line {line_no}: {content[:180]}...")
