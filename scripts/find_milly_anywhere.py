import os

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

for root, dirs, files in os.walk(project_dir):
    for file in files:
        if file.endswith((".py", ".json", ".txt", ".csv", ".html")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if "3-sitssoffa-milly-be" in content:
                    print(f"Found in: {os.path.relpath(path, project_dir)}")
            except Exception as e:
                pass
