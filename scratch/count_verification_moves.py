log_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\tasks\task-1730.log"

move_count = 0
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        if "[KEEP] Moving" in line:
            move_count += 1

print(f"Total keep moves recorded in server log: {move_count}")
