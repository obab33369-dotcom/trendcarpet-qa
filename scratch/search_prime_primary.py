import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
DB_PATH = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

def main():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return
        
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("=== SEARCHING FOR PRIME AS PRIMARY ===")
    matches = []
    for item in data:
        refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
        if refs:
            primary = refs[0].lower()
            if "prime" in primary and "byr" in primary:
                matches.append(item)
                
    print(f"Found {len(matches)} prompts where Prime is primary:")
    for idx, item in enumerate(matches):
        print(f"  {idx+1}. Prompt: {item.get('prompt')[:150]}...")
        print(f"     Refs: {item.get('image_references')}")

if __name__ == "__main__":
    main()
