with open(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\9a89adb6-c2a2-4ca2-a186-3ca3c4d5681e\.system_generated\tasks\task-6145.log", "r", encoding="utf-8") as f:
    lines = f.readlines()

targets = ["100437", "85624", "109-natural", "1211-c", "eilens"]
for line in lines:
    for t in targets:
        if t in line:
            print(line.strip())
