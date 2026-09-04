import json
import re

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
EXPORT_JSON_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow.json"

def main():
    # Load original database
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
    db_keys = set(db.keys())
    print(f"Original database contains {len(db_keys)} unique products.")

    # Load generated prompts
    with open(EXPORT_JSON_PATH, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    print(f"Generated rooms file contains {len(prompts)} prompts.")

    # Parse all tags from prompts
    referenced_ids = set()
    for item in prompts:
        tags = item["image_tags"].split("; ")
        for t in tags:
            if t.strip():
                # Extract number from tag, e.g. "@0257" -> find the matching key in db
                num = t.replace("@", "").strip()
                # Find matching key in db
                matching_key = None
                for key in db_keys:
                    if key.startswith(num + "_"):
                        matching_key = key
                        break
                if matching_key:
                    referenced_ids.add(matching_key)
                else:
                    # Let's print tag if not found
                    print(f"Warning: could not resolve tag {t}")

    print(f"Total unique database products successfully featured: {len(referenced_ids)}")
    
    # Identify any missing products
    missing = db_keys - referenced_ids
    if missing:
        print(f"Warning: {len(missing)} products were missed:")
        for m in sorted(list(missing)):
            print(f"  - {m}")
    else:
        print("🎉 SUCCESS! 100% of the 209 products in the inventory are featured in the generated prompts!")

if __name__ == "__main__":
    main()
