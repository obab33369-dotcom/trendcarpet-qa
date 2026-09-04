import os

print("--- PROJECT SEARCH FOR 'MONTMARTRE' ---")
count = 0
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith((".py", ".json", ".txt", ".csv")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if "montmartre" in content.lower():
                    print(f"Found in {path}")
                    count += 1
            except Exception:
                pass
print(f"Total files with 'montmartre': {count}")
