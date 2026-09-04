import os

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    log_path = os.path.join(PROJECT_DIR, "full_cleanup_run.log")
    if not os.path.exists(log_path):
        print("Log not found.")
        return
        
    print("Searching log...")
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if "newcastle" in line.lower():
                print(line.strip())

if __name__ == "__main__":
    main()
