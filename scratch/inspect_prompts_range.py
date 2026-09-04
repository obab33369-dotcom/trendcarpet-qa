import os
import re

DB_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"

def main():
    print(f"Scanning for prompt databases and files in {DB_DIR}...")
    for item in os.listdir(DB_DIR):
        path = os.path.join(DB_DIR, item)
        if os.path.isfile(path) and ("prompt" in item or "ready" in item or "rooms" in item) and item.endswith((".txt", ".json", ".csv")):
            size_mb = os.path.getsize(path) / (1024.0 * 1024.0)
            print(f"  File: {item} - Size: {size_mb:.2f} MB")
            
            # Let's see if we can find how many prompts it has or the range of indices
            if item.endswith(".txt") and "prompt" in item:
                # Count lines and check range of numbers
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    print(f"    Total lines: {len(lines)}")
                    # Check first and last prompt numbers
                    prefixes = []
                    for line in lines[:1000] + lines[-1000:]:
                        m = re.match(r"^(\d+)\s*-\s*", line.strip())
                        if m:
                            prefixes.append(int(m.group(1)))
                    if prefixes:
                        print(f"    Sample prefix range: {min(prefixes)} to {max(prefixes)}")
                except Exception as e:
                    print(f"    Error reading: {e}")
                    
if __name__ == "__main__":
    main()
