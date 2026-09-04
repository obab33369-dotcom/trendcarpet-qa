import os

search_terms = ["temporary", "topaz", "ftp_upload", "upload_cropped"]
dir_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

for filename in os.listdir(dir_path):
    if filename.endswith(".py"):
        filepath = os.path.join(dir_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                for term in search_terms:
                    if term.lower() in content.lower():
                        # Find line numbers
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if term.lower() in line.lower():
                                print(f"{filename}:{i+1}: {line.strip()}")
        except Exception as e:
            pass
