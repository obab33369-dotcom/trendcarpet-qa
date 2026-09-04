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
                        
                        # Print step details
                        print(f"Line {idx} (Step {obj.get('step_index')}): {created_at} [{src}/{t}]")
                        
                        # If model response, show brief thinking/content
                        if src == 'MODEL' and t == 'PLANNER_RESPONSE':
                            thinking = obj.get('thinking', '')
                            content = obj.get('content', '')
                            if thinking:
                                print(f"  Thinking: {thinking[:150]}...")
                            if content:
                                print(f"  Content: {content[:150]}...")
                    except Exception as e:
                        pass
    else:
        print("Transcript not found")

if __name__ == "__main__":
    main()
