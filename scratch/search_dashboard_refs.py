import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

for root, dirs, files in os.walk(WORKSPACE_DIR):
    for f in files:
        if f.endswith(".py"):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8') as file:
                    content = file.read()
                if "turboflow_dashboard" in content:
                    print(f"Found reference in {p}")
            except Exception:
                pass
