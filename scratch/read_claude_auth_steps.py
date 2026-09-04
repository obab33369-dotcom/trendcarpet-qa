import os
import json

log_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\claude_setup_log.txt"

steps_to_extract = [277, 278, 279, 280, 281, 282, 283, 284, 285, 298, 299, 300, 301, 302, 303, 304, 305]

if os.path.exists(log_path):
    print("Reading log...")
    current_step_num = -1
    current_step_content = []
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("=================== STEP"):
                if current_step_num in steps_to_extract:
                    print(f"\n=================== STEP {current_step_num} ===================")
                    print("".join(current_step_content))
                current_step_num = int(line.split("STEP")[1].split("(")[0].strip())
                current_step_content = []
            else:
                current_step_content.append(line)
                
        # Final step check
        if current_step_num in steps_to_extract:
            print(f"\n=================== STEP {current_step_num} ===================")
            print("".join(current_step_content))
else:
    print("Log not found")
