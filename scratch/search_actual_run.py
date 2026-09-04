import os
import json

log_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs"
path = os.path.join(log_dir, 'transcript.jsonl')

def main():
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                try:
                    obj = json.loads(line)
                    tcalls = obj.get('tool_calls', [])
                    if not tcalls and 'tool_calls' in obj:
                        tcalls = obj['tool_calls']
                    
                    for tc in tcalls:
                        if tc.get('name') == 'run_command':
                            cmd = tc.get('args', {}).get('CommandLine', '')
                            if 'execute_full_catalog_sorting' in cmd:
                                print(f"Line {idx} (Step {obj.get('step_index')}): {obj.get('created_at')} -> COMMAND: {cmd}")
                                # Look for next step for output
                                break
                except Exception:
                    pass
    else:
        print("Transcript not found")

if __name__ == "__main__":
    main()
