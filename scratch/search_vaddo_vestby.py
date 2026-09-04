import os
import json

def search_files(directory, term):
    results = []
    for root, dirs, files in os.walk(directory):
        # Skip some dirs
        if "venv" in root or ".git" in root or ".gemini" in root:
            continue
        for file in files:
            if file.endswith(('.py', '.json', '.txt', '.md', '.csv')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if term.lower() in content.lower():
                            # Find lines
                            lines = content.split('\n')
                            for idx, line in enumerate(lines):
                                if term.lower() in line.lower():
                                    results.append((path, idx + 1, line.strip()[:150]))
                except Exception as e:
                    pass
    return results

def main():
    workspace = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
    
    print("=== SEARCH FOR 'vadd' ===")
    results_vadd = search_files(workspace, "vadd")
    for r in results_vadd[:30]:
        print(f"{os.path.basename(r[0])}:{r[1]} -> {r[2]}")
        
    print("\n=== SEARCH FOR 'vestby' ===")
    results_vestby = search_files(workspace, "vestby")
    for r in results_vestby[:30]:
        print(f"{os.path.basename(r[0])}:{r[1]} -> {r[2]}")

if __name__ == "__main__":
    main()
