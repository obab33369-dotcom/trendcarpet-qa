import os
import re
import datetime
from collections import defaultdict

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def analyze_timestamps():
    dirs_to_scan = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    files_info = []
    for d in dirs_to_scan:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            path = os.path.join(d, f)
            try:
                stat = os.stat(path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files_info.append({
                    "filename": f,
                    "dir": os.path.basename(d) or "root",
                    "mtime": mtime,
                    "path": path
                })
            except Exception as e:
                pass

    if not files_info:
        print("No image files found in OneDrive directories.")
        return

    print(f"Scanned {len(files_info)} images.")
    
    # Sort files chronologically
    files_info.sort(key=lambda x: x["mtime"])
    
    # Group into clusters where gap between consecutive files is > 2 hours
    clusters = []
    current_cluster = [files_info[0]]
    
    for item in files_info[1:]:
        time_diff = (item["mtime"] - current_cluster[-1]["mtime"]).total_seconds() / 3600.0
        if time_diff > 2.0:
            clusters.append(current_cluster)
            current_cluster = [item]
        else:
            current_cluster.append(item)
    clusters.append(current_cluster)
    
    print(f"\nFound {len(clusters)} temporal clusters:")
    for idx, cluster in enumerate(clusters):
        start_time = cluster[0]["mtime"]
        end_time = cluster[-1]["mtime"]
        size = len(cluster)
        print(f"Cluster {idx+1}: {size} images | Start: {start_time} | End: {end_time}")
        
        # Show sample files in the cluster
        prefixes = []
        for item in cluster[:10]:
            m = re.match(r"^(\d+)", item["filename"])
            if m:
                prefixes.append(m.group(1))
        print(f"  Sample prefixes: {', '.join(prefixes[:10])}...")

if __name__ == "__main__":
    analyze_timestamps()
