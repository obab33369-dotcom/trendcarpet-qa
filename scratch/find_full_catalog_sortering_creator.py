import os

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    print("Searching for 'Reforma-Full-Catalog-sortering'...")
    for root, dirs, files in os.walk(PROJECT_DIR):
        for f in files:
            if f.endswith(('.py', '.log', '.txt', '.md')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                        if "reforma-full-catalog-sortering" in file.read().lower():
                            print(f"Found in: {os.path.relpath(path, PROJECT_DIR)}")
                except Exception:
                    pass

if __name__ == "__main__":
    main()
