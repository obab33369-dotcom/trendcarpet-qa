import os

log_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\claude_setup_log.txt"

if os.path.exists(log_path):
    print("Reading log...")
    commands_run = []
    with open(log_path, 'r', encoding='utf-8') as f:
        current_step = ""
        for line in f:
            if line.startswith("=================== STEP"):
                current_step = line.strip()
            if "claude" in line.lower() and ("powershell" in line.lower() or "cmd" in line.lower() or "run_command" in line.lower() or "commandline" in line.lower()):
                commands_run.append((current_step, line.strip()))
                
    print(f"Total commands mentioning 'claude': {len(commands_run)}")
    for step, cmd in commands_run[:30]:
        print(f"{step}: {cmd[:200]}")
else:
    print("Log not found")
