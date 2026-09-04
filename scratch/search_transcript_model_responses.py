import json
import os

transcript_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    print("Transcript not found.")
else:
    print("Reading transcript...")
    steps = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass
                
    # Search for model responses around the time the user asked request 8 or 9
    for i, step in enumerate(steps):
        if step.get("type") == "USER_INPUT":
            content = step.get("content", "")
            if "gtt igenom" in content or "massa fler bilder" in content or "felsorteringar" in content:
                print(f"\n--- USER INPUT STEP {step.get('step_index')} ---")
                print(content[:200])
                # Find the next model response
                for j in range(i + 1, len(steps)):
                    next_step = steps[j]
                    if next_step.get("source") == "MODEL" and next_step.get("type") == "PLANNER_RESPONSE":
                        print(f"--- MODEL RESPONSE STEP {next_step.get('step_index')} ---")
                        print(next_step.get("content", "")[:600])
                        break
