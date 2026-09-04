import os
import re

log_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\fable_transcripts_log.txt"
out_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\fable5_extracted_design_review.md"

if os.path.exists(log_path):
    print("Reading log...")
    responses = []
    
    with open(log_path, 'r', encoding='utf-8') as f:
        current_header = ""
        current_content = []
        is_collecting = False
        
        for line in f:
            if line.startswith("==================="):
                if is_collecting:
                    responses.append((current_header, "".join(current_content)))
                current_header = line.strip()
                current_content = []
                is_collecting = False
            else:
                if "=== CLAUDE FABLE 5" in line:
                    is_collecting = True
                if is_collecting:
                    current_content.append(line)
                    
        # Final append
        if is_collecting:
            responses.append((current_header, "".join(current_content)))
            
    print(f"Total responses found: {len(responses)}")
    with open(out_file, 'w', encoding='utf-8') as out:
        out.write("# Extracted Claude Fable 5 Design Reviews\n\n")
        out.write("These reviews were found in the historical logs of this session.\n\n")
        for header, content in responses:
            out.write(f"## {header}\n\n")
            out.write(content)
            out.write("\n\n---\n\n")
    print(f"Successfully wrote Fable 5 reviews to: {out_file}")
else:
    print("Log not found")
