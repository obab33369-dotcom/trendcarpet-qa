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
        
    print("=== SEARCHING DATABASE ===")
    sakai_matches = []
    prime_matches = []
    
    for item in data:
        prompt = item.get('prompt', '')
        refs = item.get('image_references', '')
        
        if "sakai" in prompt.lower() or "sakai" in refs.lower():
            sakai_matches.append(item)
        if "prime" in prompt.lower() or "prime" in refs.lower():
            prime_matches.append(item)
            
    print(f"Found {len(sakai_matches)} prompts referencing Sakai:")
    for idx, item in enumerate(sakai_matches[:10]):
        print(f"  {idx+1}. Prompt: {item.get('prompt')[:150]}...")
        print(f"     Refs: {item.get('image_references')}")
        
    print(f"\nFound {len(prime_matches)} prompts referencing Prime:")
    for idx, item in enumerate(prime_matches[:10]):
        print(f"  {idx+1}. Prompt: {item.get('prompt')[:150]}...")
        print(f"     Refs: {item.get('image_references')}")

if __name__ == "__main__":
    main()
