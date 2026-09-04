with open(r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\9a89adb6-c2a2-4ca2-a186-3ca3c4d5681e\.system_generated\tasks\task-6145.log", "r", encoding="utf-8") as f:
    lines = f.readlines()

count = 0
for line in lines:
    if "SKU:" in line:
        print(line.strip())
        count += 1
        if count >= 100:
            print("... visade de första 100 raderna ...")
            break
