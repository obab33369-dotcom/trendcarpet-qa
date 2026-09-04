import os
import json

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\d1c24698-ad94-41e4-9157-e642eccd4b9d\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    print(f"Transcript not found at: {transcript_path}")
else:
    print(f"Reading opus subagent transcript: {transcript_path}")
    steps = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass
    print(f"Total steps: {len(steps)}")
    
    # Print the initial prompt, and last assistant outputs
    if steps:
        first_step = steps[0]
        print("\n--- FIRST STEP ---")
        print(str(first_step.get("content", ""))[:1000])
        
        # Look for the last assistant response (type PLANNER_RESPONSE or MODEL)
        last_responses = [s for s in steps if s.get("type") in ["PLANNER_RESPONSE", "MODEL"] or s.get("source") == "MODEL"]
        if last_responses:
            print(f"\n--- LAST ASSISTANT RESPONSE (out of {len(last_responses)}) ---")
            print(str(last_responses[-1].get("content", ""))[:1500])
        else:
            print("\nNo assistant response found yet.")
