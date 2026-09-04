import os

LOG_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\tasks\task-2191.log"

def main():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        print(f"Total lines: {len(lines)}")
        print("Tail of log:")
        for line in lines[-30:]:
            print(line, end='')
    else:
        print(f"Log path does not exist: {LOG_PATH}")

if __name__ == "__main__":
    main()
