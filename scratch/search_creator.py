import os
import json

log_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs"
path = os.path.join(log_dir, 'transcript.jsonl')

def main():
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                if 'Reforma-Full-Catalog-sortering' in line:
                    try:
                        obj = json.loads(line)
                        t = obj.get('type')
                        src = obj.get('source')
                        created_at = obj.get('created_at')
                        
                        # Check if it has tool_calls
                        tcalls = obj.get('tool_calls', [])
                        if not tcalls and 'tool_calls' in obj:
                            tcalls = obj['tool_calls']
                            
                        cmd = ""
                        if tcalls:
                            for tc in tcalls:
                                if tc.get('name') == 'run_command':
                                    cmd = tc.get('args', {}).get('CommandLine', '')
                                    break
                        
                        if cmd:
                            print(f"Line {idx}: {created_at} [{src}/{t}] -> {cmd}")
                        elif t == 'RUN_COMMAND':
                            print(f"Line {idx}: {created_at} [RUN_COMMAND_STEP] -> {obj.get('content', '')[:150]}")
                    except Exception as e:
                        print(f"Error parsing line {idx}: {e}")
    else:
        print("Transcript not found")

if __name__ == "__main__":
    main()
