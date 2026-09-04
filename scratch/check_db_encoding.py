import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

for db_name in ['rooms_turboflow_batch1.json', 'rooms_turboflow_batch2.json', 'rooms_turboflow_full_catalog.json']:
    path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', db_name)
    if not os.path.exists(path):
        continue
    with open(path, 'rb') as f:
        content = f.read()
    
    print(f"\n=== {db_name} ===")
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            decoded = content.decode(enc)
            # Find an entry with 'bäddsoffa' or double-encoded characters
            sample_pos = decoded.find("bäddsoffa")
            if sample_pos == -1:
                sample_pos = decoded.find("bÃ¤ddsoffa")
            if sample_pos == -1:
                sample_pos = decoded.find("baddsoffa")
            
            sample = ""
            if sample_pos != -1:
                sample = decoded[max(0, sample_pos-20):sample_pos+50]
            print(f"  {enc}: success. Sample: {repr(sample)}")
        except Exception as e:
            print(f"  {enc}: failed with {type(e).__name__}")
