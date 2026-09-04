import os

print("--- PROJECT SEARCH FOR 79420/79421/79422 ---")
count = 0
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith((".py", ".json", ".txt", ".csv")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for sku in ["79420", "79421", "79422"]:
                    if sku in content:
                        print(f"Found {sku} in {path}")
                        count += 1
            except Exception:
                pass
print(f"Search completed. Found in {count} files.")
