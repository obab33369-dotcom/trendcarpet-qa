import os

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_dir(directory):
    for root, dirs, files in os.walk(directory):
        if "__pycache__" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as file:
                        for line_num, line in enumerate(file, 1):
                            if "Reforma-Full-Catalog-sortering" in line:
                                print(f"{os.path.relpath(path, PROJECT_DIR)}:L{line_num} | {line.strip()}")
                except Exception:
                    pass

def main():
    print("Searching for 'Reforma-Full-Catalog-sortering' in Python files...")
    search_dir(PROJECT_DIR)
    
if __name__ == "__main__":
    main()
