import os
import re
import datetime

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def sample_clusters():
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
                    "mtime": mtime,
                    "dir": os.path.basename(d)
                })
            except Exception:
                pass

    if not files_info:
        print("No files found.")
        return

    files_info.sort(key=lambda x: x["mtime"])
    
    # Cluster
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
    
    for idx, c in enumerate(clusters):
        print(f"\nCluster {idx+1}: {len(c)} files | Dir: {c[0]['dir']} -> {c[-1]['dir']}")
        print(f"  Start: {c[0]['mtime']} | End: {c[-1]['mtime']}")
        print("  First 3 files:")
        for f in c[:3]:
            print(f"    {f['filename']} (modified: {f['mtime']})")
        print("  Last 3 files:")
        for f in c[-3:]:
            print(f"    {f['filename']} (modified: {f['mtime']})")

if __name__ == "__main__":
    sample_clusters()
