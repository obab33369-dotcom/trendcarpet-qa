import os
import json
import re

tf_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

files_to_check = [
    "prompts_only_yesterday.txt",
    "turboflow_ready_yesterday.json"
]

for filename in files_to_check:
    path = os.path.join(tf_dir, filename)
    if os.path.exists(path):
        print(f"\nAnalyzing file: {filename}")
        if filename.endswith(".txt"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(500)
                    print("First 500 characters of yesterday prompts:")
                    print(content)
                    
                    # Find all numbers at the start of prompts
                    f.seek(0)
                    numbers = []
                    for line in f:
                        m = re.match(r"^(\d+)", line.strip())
                        if m:
                            numbers.append(int(m.group(1)))
                    if numbers:
                        print(f"Total prompt numbers: {len(numbers)}")
                        print(f"Number range: {min(numbers)} to {max(numbers)}")
            except Exception as e:
                print("Error reading txt:", e)
        elif filename.endswith(".json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Type of JSON: {type(data)}")
                    if isinstance(data, list):
                        print(f"Length of list: {len(data)}")
                        # check prompt numbers
                        numbers = []
                        for item in data:
                            prompt = item.get('prompt', '')
                            m = re.match(r"^(\d+)", prompt.strip())
                            if m:
                                numbers.append(int(m.group(1)))
                        if numbers:
                            print(f"Total prompt numbers in JSON: {len(numbers)}")
                            print(f"Number range in JSON: {min(numbers)} to {max(numbers)}")
                    elif isinstance(data, dict):
                        print(f"Keys: {list(data.keys())[:10]}")
            except Exception as e:
                print("Error reading JSON:", e)
    else:
        print(f"File {filename} does not exist.")
