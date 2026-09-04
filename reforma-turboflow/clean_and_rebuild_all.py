import os
import sys
import json
import shutil
import re
from PIL import Image

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
SORTED_DIR = os.path.join(PICS_DIR, "sorterat_efter_mobel")
UPSCALED_DIR = os.path.join(PICS_DIR, "sorterat_efter_mobel_1x1_2000px")

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
ROOMS_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow.json"

TEST_FURNITURE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_furniture"
TEST_RUGS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_rugs"

# Determine safe Pillow filter
if hasattr(Image, 'Resampling'):
    LANCZOS_FILTER = Image.Resampling.LANCZOS
elif hasattr(Image, 'LANCZOS'):
    LANCZOS_FILTER = Image.LANCZOS
else:
    LANCZOS_FILTER = Image.ANTIALIAS

def get_beautiful_name(slug):
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

def extract_true_suffix(filename):
    """
    Extracts the correct prompt index and its unique suffix from the filename.
    E.g. '093-architectural-digest-style-093b.png' -> '093b'
    E.g. '011-architectural-digest-style-011 (1).png' -> '011 (1)'
    E.g. '217-architectural-digest-style-052.png' -> '217'
    """
    base, _ = os.path.splitext(filename)
    m_lead = re.match(r"^(\d+)", base)
    if not m_lead:
        return None
    lead_num = m_lead.group(1)
    
    parts = base.split('-')
    if parts:
        last_part = parts[-1]
        m_suffix = re.match(r"^\d+(.*)$", last_part)
        if m_suffix:
            pure_suffix = m_suffix.group(1)
            return f"{lead_num}{pure_suffix}"
            
    return lead_num

def rebuild_pipeline():
    print("==================================================")
    print("    STARTING CLEAN PIPELINE REBUILD (PNG FORMAT)  ")
    print("==================================================")
    
    # 1. Clean slate
    if os.path.exists(SORTED_DIR):
        print("🧹 Deleting existing sorted folder...")
        shutil.rmtree(SORTED_DIR, ignore_errors=True)
    if os.path.exists(UPSCALED_DIR):
        print("🧹 Deleting existing upscaled folder...")
        shutil.rmtree(UPSCALED_DIR, ignore_errors=True)
        
    os.makedirs(SORTED_DIR, exist_ok=True)
    os.makedirs(UPSCALED_DIR, exist_ok=True)

    # 2. Load databases
    print("📂 Loading database files...")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        furniture_db = json.load(f)
    with open(ROOMS_PATH, "r", encoding="utf-8") as f:
        rooms = json.load(f)

    # 3. Map IDs to beautiful names
    id_to_name = {}
    id_to_key = {}
    for key in furniture_db.keys():
        parts = key.split('_', 1)
        if len(parts) >= 2:
            item_id = parts[0]
            rest = parts[1]
            name_part = os.path.splitext(rest)[0]
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
        m = re.match(r"^(\d+)\s*-", prompt_text)
        if m:
            prompt_num = int(m.group(1))
            tags_str = r.get("image_tags", "")
            tags = [t.strip().replace("@", "") for t in tags_str.split(";") if t.strip()]
            
            names = []
            for tag in tags:
                name = id_to_name.get(tag)
                if name:
                    names.append(name)
            prompt_to_names[prompt_num] = names

    # 5. Scan raw renders in main directory
    image_files = sorted([f for f in os.listdir(PICS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    print(f"📸 Found {len(image_files)} raw renders to process.")
    
    copied_renders = 0
    active_folders = set()

    # 6. Copy and Rename Renders
    print("\n🚚 Sorting and renaming renders in sorterat_efter_mobel...")
    for filename in image_files:
        m = re.match(r"^(\d+)", filename)
        if not m:
            continue
            
        prompt_num = int(m.group(1))
        furniture_pieces = prompt_to_names.get(prompt_num)
        if not furniture_pieces:
            continue
            
        src_path = os.path.join(PICS_DIR, filename)
        true_suffix = extract_true_suffix(filename)
        
        for furniture in furniture_pieces:
            dest_folder = os.path.join(SORTED_DIR, furniture)
            os.makedirs(dest_folder, exist_ok=True)
            active_folders.add(furniture)
            
            # Construct beautiful clean filename, e.g. "Barstol_Borås_Brun_Svart-093b-IN.png"
            prefix = furniture.replace(" ", "_")
            new_filename = f"{prefix}-{true_suffix}-IN.png"
            dest_path = os.path.join(dest_folder, new_filename)
            
            shutil.copy2(src_path, dest_path)
            copied_renders += 1

    # 7. Copy Product Reference Photos as uncropped PNGs
    print("\n📦 Copying original reference photos as uncropped PNGs...")
    copied_refs = 0
    for item_id, key in id_to_key.items():
        beautiful_name = id_to_name[item_id]
        if beautiful_name not in active_folders:
            continue
            
        ref_src_path = None
        path_furn = os.path.join(TEST_FURNITURE_DIR, key)
        if os.path.exists(path_furn):
            ref_src_path = path_furn
        else:
            path_rugs = os.path.join(TEST_RUGS_DIR, key)
            if os.path.exists(path_rugs):
                ref_src_path = path_rugs
                
        if ref_src_path:
            dest_folder = os.path.join(SORTED_DIR, beautiful_name)
            prefix = beautiful_name.replace(" ", "_")
            ref_dest_filename = f"00_ORIGINAL_{prefix}.png"
            ref_dest_path = os.path.join(dest_folder, ref_dest_filename)
            
            try:
                # Convert WebP original to PNG on the fly!
                with Image.open(ref_src_path) as img:
                    img.save(ref_dest_path, format="PNG")
                copied_refs += 1
            except Exception as e:
                print(f"   Error converting reference photo for '{beautiful_name}': {e}")

    # 8. Rebuild upscaled copy (sorterat_efter_mobel_1x1_2000px)
    print("\n🖼️ Building 1:1, 2000x2000px square renders in sorterat_efter_mobel_1x1_2000px...")
    processed_up_renders = 0
    copied_up_refs = 0
    
    for cat in sorted(list(active_folders)):
        src_cat_path = os.path.join(SORTED_DIR, cat)
        dest_cat_path = os.path.join(UPSCALED_DIR, cat)
        os.makedirs(dest_cat_path, exist_ok=True)
        
        files = os.listdir(src_cat_path)
        for f in files:
            src_file_path = os.path.join(src_cat_path, f)
            dest_file_path = os.path.join(dest_cat_path, f)
            
            if f.startswith("00_ORIGINAL_"):
                # Copy the uncropped original comparison photo directly!
                shutil.copy2(src_file_path, dest_file_path)
                copied_up_refs += 1
            else:
                # Crop render to 1:1 and upscale to 2000x2000 px!
                try:
                    with Image.open(src_file_path) as img:
                        width, height = img.size
                        min_dim = min(width, height)
                        left = (width - min_dim) / 2
                        top = (height - min_dim) / 2
                        right = (width + min_dim) / 2
                        bottom = (height + min_dim) / 2
                        
                        cropped_img = img.crop((left, top, right, bottom))
                        upscaled_img = cropped_img.resize((2000, 2000), LANCZOS_FILTER)
                        upscaled_img.save(dest_file_path, format="PNG")
                    processed_up_renders += 1
                except Exception as e:
                    print(f"   Error upscaling render '{f}' in '{cat}': {e}")

    print("\n==================================================")
    print("             REBUILD PIPELINE COMPLETED!          ")
    print("==================================================")
    print(f"📂 Output Folder 1: {SORTED_DIR}")
    print(f"📂 Output Folder 2 (Square 2000px): {UPSCALED_DIR}")
    print(f"📝 Renders sorted & renamed: {copied_renders}")
    print(f"🖼️ Reference photos copied (PNG): {copied_refs}")
    print(f"✨ Square 1:1 renders generated (2000px): {processed_up_renders}")
    print(f"🖼️ Square references copied (Uncropped): {copied_up_refs}")
    print("==================================================")

if __name__ == "__main__":
    rebuild_pipeline()
