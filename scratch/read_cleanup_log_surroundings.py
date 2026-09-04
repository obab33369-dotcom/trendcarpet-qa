import os

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    log_path = os.path.join(PROJECT_DIR, "full_cleanup_run.log")
    if not os.path.exists(log_path):
        print("Log not found.")
        return
        
    print("Reading log surroundings...")
    lines = []
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    for idx, line in enumerate(lines):
        if "Bokhylla Newcastle Svart (NEWCASTLE-BLACK)" in line:
            start = max(0, idx - 5)
            end = min(len(lines), idx + 20)
            print(f"--- Lines {start} to {end} ---")
            for i in range(start, end):
                print(f"{i}: {lines[i].strip()}")
            print("-" * 50)

if __name__ == "__main__":
    main()
