import json
import os

ROOMS_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow_batch2.json"
DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"

if not os.path.exists(ROOMS_PATH) or not os.path.exists(DB_PATH):
    print("Files not found")
else:
    with open(ROOMS_PATH, "r", encoding="utf-8") as f:
        rooms = json.load(f)
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    print(f"Analyzing {len(rooms)} room packages with {len(db)} products...")
    
    # Track usage frequency for each product ID (starts with 0001, etc.)
    usage = {}
    for filename in db.keys():
        parts = filename.split('_', 1)
        if len(parts) >= 1:
            usage[parts[0]] = 0
            
    # Count occurrences of tags in rooms
    total_tags = 0
    for r in rooms:
        tags_str = r.get("image_tags", "")
        tags = [t.strip().replace("@", "") for t in tags_str.split(";") if t.strip()]
        for tag in tags:
            if tag in usage:
                usage[tag] += 1
                total_tags += 1
            else:
                print(f"  ⚠️ Warning: Tag {tag} not in Batch 2 database!")

    print(f"Total tag occurrences counted: {total_tags}")
    
    # Sort usages
    sorted_usages = sorted(usage.items(), key=lambda x: x[1], reverse=True)
    
    print("\nProduct Repetitions Breakdown:")
    print(f"  • Max repetitions for a single item: {sorted_usages[0][1]} times")
    print(f"  • Min repetitions for a single item: {sorted_usages[-1][1]} times")
    
    # Group items by frequency
    freq_groups = {}
    for item_id, count in sorted_usages:
        freq_groups[count] = freq_groups.get(count, 0) + 1
        
    print("\nDistribution Frequency Groups:")
    for freq in sorted(freq_groups.keys(), reverse=True):
        print(f"  • {freq_groups[freq]} items appeared exactly {freq} times in renders")
        
    # Let's check rugs specifically
    # Rugs start with 2
    rug_usages = {item_id: count for item_id, count in usage.items() if item_id.startswith('2')}
    print(f"\nSpecific Rugs Usage ({len(rug_usages)} rugs total):")
    for rug_id, count in sorted(rug_usages.items(), key=lambda x: x[1], reverse=True):
        print(f"  • Rug @{rug_id}: {count} times")
        
    # Let's check lamps specifically
    # Lamps in batch 2 (let's check IDs starting with lamp keywords or from db)
    # Taklampa, bordslampa, golvlampa
    lamp_ids = []
    for filename in db.keys():
        if any(x in filename.lower() for x in ['lampa', 'taklampa', 'bordslampa', 'golvlampa']):
            lamp_ids.append(filename.split('_', 1)[0])
    lamp_usages = {item_id: usage[item_id] for item_id in lamp_ids if item_id in usage}
    print(f"\nSpecific Lamps Usage ({len(lamp_usages)} lamps total):")
    for lamp_id, count in sorted(lamp_usages.items(), key=lambda x: x[1], reverse=True):
        print(f"  • Lamp @{lamp_id}: {count} times")
