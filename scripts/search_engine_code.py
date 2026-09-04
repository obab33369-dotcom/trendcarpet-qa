import os

ENGINE_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\engine.py"

if not os.path.exists(ENGINE_PATH):
    print("engine.py not found")
else:
    with open(ENGINE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    print("Core classes or functions in engine.py:")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "def " in line or "class " in line:
            print(f"  Line {i+1:03d}: {line.strip()}")
            
    print("\nLooking for environment settings and keywords:")
    for i, line in enumerate(lines):
        if "environment" in line.lower() or "template" in line.lower():
            if "def " in line or "=" in line:
                print(f"  Line {i+1:03d}: {line.strip()[:100]}")
