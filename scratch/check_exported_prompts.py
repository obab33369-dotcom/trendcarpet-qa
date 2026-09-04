import os

prompts_file = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\prompts_only_full_catalog_batch3.txt"

print("=== PROMPTS ONLY ENTRIES ===")
if os.path.exists(prompts_file):
    with open(prompts_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("3008 -") or line.startswith("3012 -"):
                print(line.strip())
                print("-" * 50)
else:
    print("Prompts file not found.")
