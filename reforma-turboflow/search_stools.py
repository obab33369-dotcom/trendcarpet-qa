import os
import re

directory = r"c:/Users/AndronikLindgren/.gemini/antigravity/scratch/Projects/REFORMA/reforma-turboflow"

for filename in os.listdir(directory):
    if filename.endswith(".py"):
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if "stool" in content.lower() or "pall" in content.lower():
                    print(f"=== Found in {filename} ===")
                    lines = content.splitlines()
                    for idx, line in enumerate(lines):
                        if "stool" in line.lower() or "pall" in line.lower() or "puff" in line.lower():
                            if any(k in line.lower() for k in ["size", "fill", "target", "0.", "class"]):
                                print(f"  Line {idx+1}: {line.strip()}")
        except Exception as e:
            pass
