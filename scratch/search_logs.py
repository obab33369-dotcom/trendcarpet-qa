import os

LOG_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\full_cleanup_run.log"

def main():
    if not os.path.exists(LOG_PATH):
        print("Log file not found.")
        return
        
    print("Searching log file...")
    found = 0
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "matgrupp28" in line:
                print(line.strip())
                found += 1
                if found > 50:
                    print("... too many matches, truncating ...")
                    break
                    
    if found == 0:
        print("No occurrences of 'matgrupp28' found in log file.")

if __name__ == "__main__":
    main()
