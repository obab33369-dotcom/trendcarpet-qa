import re

log_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\tasks\task-1917.log"

clean_copies = 0
discard_copies = 0
deletions = 0

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        if "Successfully copied" in line:
            # Check if it mentions a count
            print(line.strip())
        elif "Successfully deleted" in line:
            print(line.strip())
        elif "Copied" in line and "reference" in line:
            print(line.strip())
            
        # Count lines containing paths
        if "Reforma-Full-Catalog-sortering-borttagna" in line:
            if "copied" in line.lower() or "copying" in line.lower():
                discard_copies += 1
            elif "deleting" in line.lower() or "deleted" in line.lower() or "delete" in line.lower():
                deletions += 1
        elif "Reforma-Full-Catalog-sortering" in line:
            if "copied" in line.lower() or "copying" in line.lower():
                clean_copies += 1

print(f"\nAnalyzed paths in log:")
print(f"  - Copies to Clean: {clean_copies}")
print(f"  - Copies to Discard: {discard_copies}")
