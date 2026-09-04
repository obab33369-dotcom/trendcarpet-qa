import json
import os

search_key = "hydra"
json_files = [
    "rooms_turboflow.json",
    "rooms_turboflow_batch1.json",
    "rooms_turboflow_batch2.json",
    "rooms_turboflow_full_catalog.json",
    "turboflow_ready.json",
    "turboflow_ready_batch2.json",
    "turboflow_ready_full_catalog.json"
]

for jf in json_files:
    if os.path.exists(jf):
        with open(jf, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                count = 0
                samples = []
                for idx, row in enumerate(data):
                    refs = row.get("image_references", "")
                    if search_key in refs.lower():
                        count += 1
                        if len(samples) < 3:
                            samples.append((idx, refs, row.get("image_tags", "")))
                print(f"File: {jf} has {count} rows containing '{search_key}' in image_references.")
                if samples:
                    print("  Samples:")
                    for idx, refs, tags in samples:
                        print(f"    Row {idx}: refs='{refs}', tags='{tags}'")
            except Exception as e:
                print(f"File: {jf} failed to parse: {e}")
