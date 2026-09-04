import os
import json
import re

TRANSCRIPT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs\transcript_full.jsonl"

def main():
    if not os.path.exists(TRANSCRIPT_PATH):
        print(f"Transcript not found at: {TRANSCRIPT_PATH}")
        return
        
    print(f"Reading transcript from {TRANSCRIPT_PATH}...")
    user_inputs = []
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    user_inputs.append(data)
            except Exception as e:
                pass
                
    print(f"Found {len(user_inputs)} user inputs in this conversation history.")
    
    for idx, inp in enumerate(user_inputs):
        content = inp.get("content", "")
        print(f"\nUser Input [{idx}]: Length = {len(content)} characters")
        print(f"Snippet: {content[:150]}...")
        
        filenames = re.findall(r"(\d+-architectural-digest-styl-\d+\.png)", content)
        print(f"  Filenames found: {len(filenames)}")
        if filenames:
            prefixes = []
            for f_name in filenames:
                m = re.match(r"^(\d+)", f_name)
                if m:
                    prefixes.append(int(m.group(1)))
            prefixes = sorted(list(set(prefixes)))
            print(f"  Prefix range: {prefixes[0]} to {prefixes[-1]}")
            
            with open(f"scratch/filenames_input_{idx}.txt", "w", encoding="utf-8") as f_out:
                for fname in filenames:
                    f_out.write(fname + "\n")
            print(f"  Saved to scratch/filenames_input_{idx}.txt")

if __name__ == "__main__":
    main()
