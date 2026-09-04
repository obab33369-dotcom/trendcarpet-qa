import os
import re

directory = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
target_words = ["image_references", "image_tags", "autotag", "tag", "reference"]

for filename in os.listdir(directory):
    if filename.endswith(".py") or filename.endswith(".js"):
        path = os.path.join(directory, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            found = []
            for word in target_words:
                if word in content:
                    found.append(word)
            if found:
                print(f"{filename}: matches {found}")
        except Exception as e:
            print(f"Error reading {filename}: {e}")
