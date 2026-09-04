import os
import sys
import json
import csv
import re
from typing import Dict, Any, List

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
CSV_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready.csv"
FLAT_JSON_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready.json"
TXT_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready.txt"
PROMPTS_ONLY_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\prompts_only.txt"

def get_short_tag(filename: str) -> str:
    match = re.match(r'^(\d+)_', filename)
    if match:
        return f"@{match.group(1)}"
    
    base, _ = os.path.splitext(filename)
    base = re.sub(r'-\d+-\w+-wonder$', '', base)
    base = base.lower().strip().replace("_", "-")
    return f"@{base[:18]}"

def get_short_filename(filename: str) -> str:
    base, ext = os.path.splitext(filename)
    match = re.match(r'^(\d+)_', base)
    if match:
        return f"{match.group(1)}{ext}"
    return filename

def clean_swedish_chars(text: str) -> str:
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text

def clean_tag_to_name(filename: str) -> str:
    base, _ = os.path.splitext(filename)
    base = re.sub(r'^\d+__*', '', base)
    base = re.sub(r'^\d+_', '', base)
    base = re.sub(r'-\d+-\w+-wonder$', '', base)
    base = re.sub(r'-\d+$', '', base)
    base = base.replace("-", " ").replace("_", " ").title()
    return clean_swedish_chars(base)

def get_lamp_type(fname: str) -> str:
    fname = fname.lower()
    if "taklampa" in fname:
        return "ceiling"
    elif "golvlampa" in fname:
        return "floor"
    return "table"

def main():
    print("Loading furniture database...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}.")
        sys.exit(1)
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
        
    print(f"Total items loaded: {len(database)}")
    
    output_rows = []
    
    # Sort database items by filename/ID to ensure consistent order
    sorted_items = sorted(database.items(), key=lambda x: x[0])
    
    for idx, (filename, item) in enumerate(sorted_items):
        row_num = idx + 1
        meta = item["metadata"]
        cat = meta["typ_av_möbel"].strip().lower()
        style = meta["stil_estetik"].strip().lower()
        tone = meta["färgton"].strip().lower()
        wood = meta["träslag"].strip().lower()
        fabric = meta["tyg_material"].strip().lower()
        
        swedish_name = clean_tag_to_name(filename)
        tag = get_short_tag(filename)
        short_file = get_short_filename(filename)
        
        # Decide lighting based on color tone
        if tone == "varm":
            lighting = "cinematic afternoon sunlight"
        else:
            lighting = "bright, crisp midday sunlight on a sunny day"
            
        # Decide location base on style
        if style == "nordisk modern":
            location = "Stockholm classic turn-of-the-century apartment in Östermalm with high ceilings, delicate plaster moldings, and views of tree-lined streets"
        elif style == "rustik":
            location = "Stockholm archipelago architect-designed cabin overlooking waters and pine trees"
        elif style == "klassisk":
            location = "Stockholm classic apartment with high decorated ceilings, ornate moldings, and courtyard views"
        else: # minimalistisk
            location = "Modern Stockholm villa with floor-to-ceiling windows facing a serene Swedish forest"
            
        # Determine specific product category detail and build prompt
        is_lamp = "lampa" in filename.lower()
        
        if is_lamp:
            lamp_type = get_lamp_type(filename)
            if lamp_type == "ceiling":
                subject = f"glowing designer ceiling pendant lamp ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} hanging low from the ceiling above a dining table and chairs, set within a {location} with {lighting}."
                bg = "In the background of the dining-living room, a designer cabinet stands against the wall, making the space feel rich and lived-in."
                extra = "Strictly preserve individual lamp material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
            elif lamp_type == "floor":
                subject = f"glowing designer floor lamp ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} standing on the oak floor in a cozy corner of a {location} with {lighting}."
                bg = "In the background of the living room, a comfortable seating area with a sofa, a designer cabinet, and a textured rug are softly visible."
                extra = "Strictly preserve individual lamp material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
            else: # table lamp
                subject = f"glowing designer table lamp ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} standing on top of a designer cabinet against the wall, set within a {location} with {lighting}."
                bg = "In the background of the living room, a cozy armchair, a textured rug, and a large window showing Stockholm rooftops are softly visible."
                extra = "Strictly preserve individual lamp material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
        
        elif cat == "stol":
            is_barstool = "barstol" in filename.lower() or "bar" in filename.lower()
            if is_barstool:
                subject = f"barstools ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} arranged around a kitchen island, set within a {location} with {lighting}."
                bg = "In the background, a designer cabinet stands against the wall, with a table lamp glowing softly, and a classic tiled stove is softly visible."
                extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
            else:
                subject = f"chairs ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} placed around a dining table, set within a {location} with {lighting}."
                bg = "In the background of the dining-living room, a designer cabinet stands against the wall, with a table lamp glowing softly, and a matching area rug lies under the table and chairs."
                extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
                
        elif cat == "bord":
            is_matbord = "matbord" in filename.lower() or "klaffbord" in filename.lower() or "bord" in filename.lower() and not any(x in filename.lower() for x in ["soffbord", "avlastnings", "sidobord", "skrivbord", "nattduksbord"])
            is_soffbord = "soffbord" in filename.lower() or "coffee" in filename.lower()
            
            if is_soffbord:
                subject = f"coffee table ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} placed in front of a modern sofa, set within a {location} with {lighting}."
                bg = "In the background of the living room, a designer cabinet stands against the wall, a floor lamp glows warmly in the corner, and a textured area rug lies under the table."
                extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
            elif is_matbord:
                subject = f"dining table ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} with elegant chairs placed around it, set within a {location} with {lighting}."
                bg = "In the background of the dining-living room, a designer cabinet stands against the wall, with a table lamp glowing softly, and a matching rectangular area rug lies under the table and chairs."
                extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
            else: # general board/console/desk
                subject = f"table ({swedish_name})"
                shot_setup = f"Architectural digest-style three-quarter view of the {subject} standing against the wall, set within a {location} with {lighting}."
                bg = "In the background of the living room, a cozy seating area, a designer cabinet, and an arty abstract poster hanging on the wall are softly visible."
                extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
                
        elif cat in ("förvaring", "frvaring"):
            subject = f"cabinet ({swedish_name})"
            shot_setup = f"Architectural digest-style three-quarter view of the {subject} standing against the wall, set within a {location} with {lighting}."
            bg = "In the background of the living room, a dining area with a table and chairs on a textured rug, and a table lamp glowing softly on the windowsill are visible."
            extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
            
        elif cat == "matta":
            subject = f"area rug ({swedish_name})"
            shot_setup = f"Architectural digest-style three-quarter view of the {subject} placed elegantly on the oak floor under a dining table and chairs, set within a {location} with {lighting}."
            bg = "In the background of the dining-living room, a designer sideboard stands against the wall, with a table lamp glowing softly, making the space feel rich and warm."
            extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Utilize chiaroscuro lighting techniques to deepen shadow definition."
            
        else: # Fallback general
            subject = f"furniture ({swedish_name})"
            shot_setup = f"Architectural digest-style three-quarter view of the {subject}, set within a {location} with {lighting}."
            bg = "In the background of the living room, a cozy dining-living space with cabinets, lamps, and a textured rug are visible."
            extra = "Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes."
            
        # Compile base prompt
        prompt = (
            f"{row_num:03d} - {shot_setup} {bg} "
            f"Dynamic three-quarter angle with controlled depth of field. "
            f"Varied gloss levels on walls and trim to enhance depth, featuring tactile micro-imperfections. "
            f"{extra} Enhance atmosphere with very subtle volumetric-dust. "
            f"Prioritize high-end material tactility and realistic light-reactive surfaces over digital polish, "
            f"real wood and stone-materials in a variety of finishes, either warm or cool. "
            f"Break the monochromatic palette with refined material contrasts, such as cool-toned stone or matte metallic finishes or grainy wood to add depth and sophisticated material friction. "
            f"No cutting-boards, no wooden plates in the kitchen, no abstract sculpture, no plants, no knick-knacks, no knick-knack.  {tag}"
        )
        
        output_rows.append({
            "prompt": prompt,
            "image_references": short_file,
            "image_tags": tag,
            "aspect_ratio": "1:1"
        })
        
    # Write to turboflow_ready.txt (prompts + tags + files)
    with open(TXT_EXPORT_PATH, "w", encoding="utf-8") as f:
        f.write("prompt,image_references,image_tags,aspect_ratio\n")
        for row in output_rows:
            # Escape quotes for CSV format in TXT
            escaped_prompt = row["prompt"].replace('"', '""')
            f.write(f'"{escaped_prompt}",{row["image_references"]},{row["image_tags"]},{row["aspect_ratio"]}\n')
            
    # Write to turboflow_ready.csv
    with open(CSV_EXPORT_PATH, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["prompt", "image_references", "image_tags", "aspect_ratio"])
        for row in output_rows:
            writer.writerow([row["prompt"], row["image_references"], row["image_tags"], row["aspect_ratio"]])
            
    # Write to prompts_only.txt (clean numbered format)
    with open(PROMPTS_ONLY_EXPORT_PATH, "w", encoding="utf-8") as f:
        for row in output_rows:
            f.write(f"{row['prompt']}\n")
            
    # Write to flat json
    with open(FLAT_JSON_EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 Rebuilt and generated prompts for ALL {len(output_rows)} products!")
    print(f"  -> TXT Export: {TXT_EXPORT_PATH}")
    print(f"  -> CSV Export: {CSV_EXPORT_PATH}")
    print(f"  -> Prompts Only: {PROMPTS_ONLY_EXPORT_PATH}")
    print(f"  -> JSON Export: {FLAT_JSON_EXPORT_PATH}")

if __name__ == "__main__":
    main()
