import os
import json

subagents = {
    "systems_architect": r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\257833d2-118d-42fe-8873-da4a65a02106\.system_generated\logs\transcript.jsonl",
    "opus_vision": r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\4838dbae-b44e-424f-9c65-7ac8e8565ff6\.system_generated\logs\transcript.jsonl"
}

for name, path in subagents.items():
    if not os.path.exists(path):
        print(f"{name} transcript not found at: {path}")
    else:
        print(f"\n=================== {name} ({os.path.basename(os.path.dirname(os.path.dirname(path)))}) ===================")
        steps = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    steps.append(json.loads(line))
                except Exception:
                    pass
        print(f"Total steps: {len(steps)}")
        if steps:
            # Print the last assistant response
            last_responses = [s for s in steps if s.get("type") in ["PLANNER_RESPONSE", "MODEL"] or s.get("source") == "MODEL"]
            if last_responses:
                print("--- LAST ASSISTANT RESPONSE ---")
                print(str(last_responses[-1].get("content", ""))[:1500])
            else:
                print("No assistant response found yet.")
