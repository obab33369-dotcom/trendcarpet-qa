import json
import csv

json_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_full_catalog.json"

try:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} rows from JSON.")
    
    # Print rows around 1525-1528 (since the prompt starts with the row number, e.g. "1525 - Architectural digest-style...")
    # Wait, the screenshot shows:
    # #215: "1525 - Architectural digest-style view..."
    # #216: "1526 - Architectural digest-style view..."
    # #217: "1527 - Architectural digest-style view..."
    # #218: "1528 - Architectural digest-style view..."
    #
    # Wait! In the screenshot, the row number in the list is "#215", "#216", "#217", "#218".
    # BUT the text inside starts with "1525 - Architectural...", "1526 - Architectural...".
    # This means the prompt text starts with "1525 - ", but the prompt ID in the UI is #215. Why?
    # Because they uploaded a batch starting from a certain row, or maybe they uploaded a subset of prompts?
    # Let's search the data for prompt texts starting with "1525 -", "1526 -", "1527 -", "1528 -".
    
    for idx, row in enumerate(data):
        prompt = row["prompt"]
        if any(prompt.startswith(f"{num:03d} -") or prompt.startswith(f"{num} -") for num in [1525, 1526, 1527, 1528]):
            print(f"\nRow index in JSON: {idx}")
            print(f"Prompt: {prompt}")
            print(f"image_references: {row['image_references']}")
            print(f"image_tags: {row['image_tags']}")
            
except Exception as e:
    print(f"Error: {e}")
