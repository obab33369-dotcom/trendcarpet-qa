import os
import sys
import json
import shutil
import re

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
SORTED_DIR = os.path.join(PICS_DIR, "sorterat_efter_mobel")

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
ROOMS_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow.json"

TEST_FURNITURE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_furniture"
TEST_RUGS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_rugs"

def get_beautiful_name(slug):
    """
    Converts a slug like 'byrå-prime-6-lådor-valnöt-mässing' into a beautifully 
    capitalized Swedish product name: 'Byrå Prime 6 Lådor Valnöt Mässing'.
    """
    words = slug.split('-')
    capitalized_words = []
    for w in words:
        if not w:
            continue
        w_lower = w.lower()
        if w_lower in ('m', 's', 'l'):
            capitalized_words.append(w.upper())
        elif w_lower == 'tv':
            capitalized_words.append('TV')
        elif 'x' in w_lower and re.match(r'^\d+x\d+', w_lower):
            capitalized_words.append(w_lower)
        else:
            capitalized_words.append(w.capitalize())
    return " ".join(capitalized_words)

def organize_images():
    print("==================================================")
    print("    STARTING TURBOFLOW FURNITURE IMAGE SORTER     ")
    print("==================================================")
    
    # 1. Validate paths
    if not os.path.exists(PICS_DIR):
        print(f"❌ Error: Renders folder not found at: {PICS_DIR}")
        return
        
    if not os.path.exists(DB_PATH) or not os.path.exists(ROOMS_PATH):
        print("❌ Error: Curation engine database files are missing!")
        return

    # 2. Load databases
    print("📂 Loading database files...")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        furniture_db = json.load(f)
    with open(ROOMS_PATH, "r", encoding="utf-8") as f:
        rooms = json.load(f)
        
    print(f"   Loaded {len(furniture_db)} furniture pieces.")
    print(f"   Loaded {len(rooms)} room packages.")

    # 3. Map IDs to beautiful names & track key names
    id_to_name = {}
    id_to_key = {}
    for key in furniture_db.keys():
        parts = key.split('_', 1)
        if len(parts) >= 2:
            item_id = parts[0]
            rest = parts[1]
            name_part = os.path.splitext(rest)[0]
            # Clean trailing Midjourney/generation hashes
            clean_slug = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', name_part)
            clean_slug = re.sub(r'-1-\w+-\w+$', '', clean_slug)
            clean_slug = re.sub(r'-\d+-\w+-\w+$', '', clean_slug)
            
            beautiful_name = get_beautiful_name(clean_slug)
            id_to_name[item_id] = beautiful_name
            id_to_key[item_id] = key

    # 4. Map prompt index to its furniture names
    prompt_to_names = {}
    for r in rooms:
        prompt_text = r.get("prompt", "")
        # Extract leading 3-digit number from prompt, e.g. "015 -"
        m = re.match(r"^(\d+)\s*-", prompt_text)
        if m:
            prompt_num = int(m.group(1))
            tags_str = r.get("image_tags", "")
            tags = [t.strip().replace("@", "") for t in tags_str.split(";") if t.strip()]
            
            # Resolve tags to beautiful names
            names = []
            for tag in tags:
                name = id_to_name.get(tag)
                if name:
                    names.append(name)
            prompt_to_names[prompt_num] = names

    # 5. Scan and copy renders
    print("\n📸 Scanning render images in OneDrive directory...")
    image_files = [f for f in os.listdir(PICS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    print(f"   Found {len(image_files)} images to sort.")
    
    # Create target directories
    os.makedirs(SORTED_DIR, exist_ok=True)
    
    copied_renders = 0
    copied_refs = 0
    errors_count = 0
    furniture_stats = {} # Count images per furniture folder
    active_folders = set() # Track folders we actually copied renders into

    for filename in image_files:
        # Extract the leading prompt number from filename, e.g., "015-architectural..." -> 15
        m = re.match(r"^(\d+)", filename)
        if not m:
            continue
            
        prompt_num = int(m.group(1))
        
        # Get furniture pieces featured in this prompt
        furniture_pieces = prompt_to_names.get(prompt_num)
        if not furniture_pieces:
            continue
            
        src_path = os.path.join(PICS_DIR, filename)
        
        for furniture in furniture_pieces:
            # Create a folder for the specific furniture item
            dest_folder = os.path.join(SORTED_DIR, furniture)
            os.makedirs(dest_folder, exist_ok=True)
            active_folders.add(furniture)
            
            dest_path = os.path.join(dest_folder, filename)
            
            try:
                # Copy render image to the furniture folder
                shutil.copy2(src_path, dest_path)
                copied_renders += 1
                furniture_stats[furniture] = furniture_stats.get(furniture, 0) + 1
            except Exception as e:
                print(f"   ❌ Error copying render {filename} to '{furniture}': {e}")
                errors_count += 1

    # 6. Copy product reference photos (Originals)
    print("\n📦 Copying original product reference photos for comparison...")
    for item_id, key in id_to_key.items():
        beautiful_name = id_to_name[item_id]
        
        # Only copy references into folders that actually have render images
        if beautiful_name not in active_folders:
            continue
            
        # Locate the physical reference webp file
        ref_src_path = None
        
        # Try test_furniture first
        path_furn = os.path.join(TEST_FURNITURE_DIR, key)
        if os.path.exists(path_furn):
            ref_src_path = path_furn
        else:
            # Try test_rugs
            path_rugs = os.path.join(TEST_RUGS_DIR, key)
            if os.path.exists(path_rugs):
                ref_src_path = path_rugs
                
        if ref_src_path:
            dest_folder = os.path.join(SORTED_DIR, beautiful_name)
            # Standardized name for the original so it appears first, t.ex. "00_ORIGINAL_Byra_Nordisk_Svart.webp"
            clean_name_underscored = beautiful_name.replace(" ", "_")
            ref_dest_filename = f"00_ORIGINAL_{clean_name_underscored}.webp"
            ref_dest_path = os.path.join(dest_folder, ref_dest_filename)
            
            try:
                shutil.copy2(ref_src_path, ref_dest_path)
                copied_refs += 1
            except Exception as e:
                print(f"   ❌ Error copying reference photo for '{beautiful_name}': {e}")
                errors_count += 1
        else:
            print(f"   ⚠️ Warning: Reference file '{key}' not found on disk.")

    # 7. Print Report
    print("\n==================================================")
    print("                SORTING COMPLETED!                ")
    print("==================================================")
    print(f"📂 Output directory: {SORTED_DIR}")
    print(f"🗂️ Unique furniture folders created: {len(furniture_stats)}")
    print(f"📝 Total render instances copied: {copied_renders}")
    print(f"🖼️ Original reference photos copied: {copied_refs}")
    if errors_count > 0:
        print(f"⚠️ Errors encountered: {errors_count}")
    print("--------------------------------------------------")
    print("Top 15 most featured furniture pieces in renders:")
    sorted_stats = sorted(furniture_stats.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_stats[:15]:
        print(f"   • {name}: {count} renders (+ original photo)")
    print("==================================================")

if __name__ == "__main__":
    organize_images()
