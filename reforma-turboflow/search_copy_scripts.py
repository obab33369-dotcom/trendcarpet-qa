import os

search_words = ["copy", "shutil"]
directory = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

for filename in os.listdir(directory):
    if filename.endswith(".py") and ("copy" in filename or "select" in filename or "build" in filename):
        path = os.path.join(directory, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"File: {filename}")
        for line in content.split("\n"):
            if any(sw in line for sw in search_words) and "import" not in line:
                print(f"  {line.strip()}")
