import os

ENGINE_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\engine.py"

if not os.path.exists(ENGINE_PATH):
    print("engine.py not found")
else:
    with open(ENGINE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    print("Files opened or referenced in engine.py:")
    for line in content.splitlines():
        if ".json" in line or ".csv" in line or "open(" in line:
            print("  ", line.strip())
