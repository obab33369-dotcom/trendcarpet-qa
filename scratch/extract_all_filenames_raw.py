import os
import json
import re

TRANSCRIPT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs\transcript_full.jsonl"

def main():
    if not os.path.exists(TRANSCRIPT_PATH):
        print("Transcript not found.")
        return
        
    user_inputs = []
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    user_inputs.append(data)
            except Exception:
                pass
                
    # We want User Input [4], which is the long list
    if len(user_inputs) <= 4:
        print(f"Only found {len(user_inputs)} user inputs in transcript. Cannot find input 4.")
        return
        
    content = user_inputs[4].get("content", "")
    print(f"User Input [4] length: {len(content)} characters.")
    
    # Let's extract any token that ends with .png, .jpg, or .jpeg or has architectural-digest in it
    # We'll split the content by lines first, and check each line
    lines = content.split("\n")
    found_tokens = []
    for line in lines:
        line_clean = line.strip()
        # Find any substring ending in .png, .jpg, etc.
        matches = re.findall(r"(\S+\.(?:png|jpg|jpeg|webp))", line_clean, re.IGNORECASE)
        for m in matches:
            found_tokens.append(m)
            
    print(f"Total files extracted using broad regex: {len(found_tokens)}")
    if found_tokens:
        print(f"First 10 tokens:")
        for t in found_tokens[:10]:
            print(f"  - {t}")
            
        print(f"Last 10 tokens:")
        for t in found_tokens[-10:]:
            print(f"  - {t}")
            
        # Let's see if there are style- vs styl- differences
        style_count = sum(1 for t in found_tokens if "style-" in t.lower())
        styl_count = sum(1 for t in found_tokens if "styl-" in t.lower())
        print(f"Count of files containing 'style-': {style_count}")
        print(f"Count of files containing 'styl-': {styl_count}")
        
        # Save all extracted filenames to a file
        with open("scratch/filenames_input_4_all.txt", "w", encoding="utf-8") as f_out:
            for t in found_tokens:
                f_out.write(t + "\n")
        print("Saved to scratch/filenames_input_4_all.txt")
        
if __name__ == "__main__":
    main()
