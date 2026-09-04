import os

log_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\fable_transcripts_log.txt"

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
            
    print(f"Total successful Fable 5 responses found: {len(responses)}")
    for header, content in responses:
        print(f"\n{header}")
        print(content[:1500] + ("..." if len(content) > 1500 else ""))
else:
    print("Log not found")
