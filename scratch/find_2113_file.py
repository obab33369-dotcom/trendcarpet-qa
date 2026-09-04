import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    found = False
    for root_dir, dirs, files in os.walk(WORKSPACE_DIR):
        for f in files:
            if "2113_matta" in f or "2113-matta" in f:
                rel = os.path.relpath(os.path.join(root_dir, f), WORKSPACE_DIR)
                print(f"Found at: {rel}")
                found = True
    if not found:
        print("Not found.")

if __name__ == "__main__":
    main()
