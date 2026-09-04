import os
import re
import datetime
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def load_db(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mapping = {}
    for item in data:
        prompt = item.get('prompt', '')
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            idx = int(m.group(1))
            mapping[idx] = {
                "prompt": prompt,
                "refs": [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
            }
    return mapping

batch1 = load_db("rooms_turboflow_batch1.json")
batch2 = load_db("rooms_turboflow_batch2.json")
full_catalog = load_db("rooms_turboflow_full_catalog.json")

def identify_clusters():
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
                    "path": path
                })
            except Exception:
                pass

    if not files_info:
        print("No files found.")
        return

    # Sort files
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
    
    # For each cluster, check database matching
    for c_idx, cluster in enumerate(clusters):
        print(f"\n================ CLUSTER {c_idx+1} ================")
        print(f"Time: {cluster[0]['mtime']} to {cluster[-1]['mtime']}")
        print(f"Total files: {len(cluster)}")
        
        # Take 5 sample files
        samples = cluster[:5] + cluster[len(cluster)//2:len(cluster)//2+3] + cluster[-5:]
        # Deduplicate
        seen_filenames = set()
        unique_samples = []
        for s in samples:
            if s["filename"] not in seen_filenames:
                seen_filenames.add(s["filename"])
                unique_samples.append(s)
                
        for s in unique_samples[:6]:
            fn = s["filename"]
            # Parse prefix and suffix
            m = re.match(r"^(\d+)", fn)
            if not m:
                continue
            prefix = int(m.group(1))
            
            m_style = re.search(r"-styl(?:e)?-(\d+)([a-z])?$", os.path.splitext(fn)[0], re.IGNORECASE)
            suffix = int(m_style.group(1)) if m_style else None
            
            print(f"\nFile: {fn} | Prefix: {prefix} | Suffix: {suffix}")
            
            # Check prefix/suffix in DBs
            # We want to see if the prefix or suffix corresponds to a valid prompt in each DB
            for db_name, db in [("Batch 1", batch1), ("Batch 2", batch2), ("Full Catalog", full_catalog)]:
                match_info = []
                # Check prefix
                if prefix in db:
                    match_info.append(f"Prefix matches DB index {prefix} (Refs: {db[prefix]['refs']})")
                # Check suffix
                if suffix is not None and suffix in db:
                    match_info.append(f"Suffix matches DB index {suffix} (Refs: {db[suffix]['refs']})")
                
                if match_info:
                    print(f"  {db_name}:")
                    for m_str in match_info:
                        print(f"    {m_str}")

if __name__ == "__main__":
    identify_clusters()
