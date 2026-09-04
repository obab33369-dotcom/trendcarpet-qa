import os

log_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\9a89adb6-c2a2-4ca2-a186-3ca3c4d5681e\.system_generated\tasks\task-6527.log"
out_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\logs_extract.txt"

if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    output = []
    
    output.append("=== Search for 99070 ===")
    for i, line in enumerate(lines):
        if "99070" in line:
            start = max(0, i - 2)
            end = min(len(lines), i + 25)
            for j in range(start, end):
                output.append(f"{j+1}: {lines[j]}")
            output.append("-" * 50)
            
    output.append("\n=== Search for rw811 ===")
    for i, line in enumerate(lines):
        if "rw811" in line:
            start = max(0, i - 2)
            end = min(len(lines), i + 25)
            for j in range(start, end):
                output.append(f"{j+1}: {lines[j]}")
            output.append("-" * 50)
            
    with open(out_path, 'w', encoding='utf-8') as f_out:
        f_out.write('\n'.join(output))
    print(f"Extraction written to {out_path}")
else:
    print("Log file not found.")
