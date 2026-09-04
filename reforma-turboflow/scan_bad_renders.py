import os
import sys
import json
import re

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Sökvägar
SORTED_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"
DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"
ROOMS_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow_batch2.json"

REPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\36bef6e6-a57c-4707-8fd1-2b263d4f0e8f\rerun_report.md"
RERUN_PROMPTS_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rerun_prompts_batch2.txt"

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

def main():
    print("==================================================")
    print("      TURBOFLOW SCANDINAVIAN QUALITY SCANNER      ")
    print("==================================================")
    
    if not os.path.exists(SORTED_DIR):
        print(f"❌ Error: Sorted directory not found: {SORTED_DIR}")
        return
    if not os.path.exists(DB_PATH) or not os.path.exists(ROOMS_PATH):
        print("❌ Error: Curation databases missing!")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
    with open(ROOMS_PATH, "r", encoding="utf-8") as f:
        rooms = json.load(f)
        
    print(f"Loaded {len(db)} products and {len(rooms)} room prompts.")
    
    # Map IDs to beautiful names
    id_to_name = {}
    name_to_id = {}
    for key in db.keys():
        parts = key.split('_', 1)
        if len(parts) >= 2:
            item_id = parts[0]
            rest = parts[1]
            name_part = os.path.splitext(rest)[0]
            clean_slug = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', name_part, flags=re.IGNORECASE)
            clean_slug = re.sub(r'-1-\w+-\w+$', '', clean_slug)
            clean_slug = re.sub(r'-\d+-\w+-\w+$', '', clean_slug)
            beautiful_name = get_beautiful_name(clean_slug)
            id_to_name[item_id] = beautiful_name
            name_to_id[beautiful_name] = item_id

    # For each product folder, scan which prompts should feature it
    # and check which ones are missing (deleted by user)
    missing_by_prompt = {} # prompt_num -> list of missing product names
    missing_by_product = {} # product_name -> list of missing prompt nums
    
    total_expected = 0
    total_missing = 0
    
    product_folders = [d for d in os.listdir(SORTED_DIR) if os.path.isdir(os.path.join(SORTED_DIR, d))]
    
    print("\n🔍 Scanning product subfolders for deleted/missing renders...")
    
    for prod_name in sorted(product_folders):
        prod_id = name_to_id.get(prod_name)
        if not prod_id:
            # Skip folders that don't match database naming (e.g. original Batch 1 folders if they differ)
            continue
            
        prod_path = os.path.join(SORTED_DIR, prod_name)
        files = os.listdir(prod_path)
        
        # Find all prompt indices that SHOULD contain this product
        expected_prompts = []
        for r_idx, r in enumerate(rooms):
            prompt_num = r_idx + 1 # 1-indexed
            tags_str = r.get("image_tags", "")
            tags = [t.strip().replace("@", "") for t in tags_str.split(";") if t.strip()]
            if prod_id in tags:
                expected_prompts.append(prompt_num)
                
        # Check files inside the folder to see if there is any render matching each expected prompt
        for p_num in expected_prompts:
            total_expected += 1
            # A render matches if it starts with the folder name prefix and has the prompt number,
            # or if it starts with prompt number e.g. "Bokhylla_Colin...-007_..."
            # Let's search using regex:
            prefix = prod_name.replace(" ", "_")
            pattern = re.compile(rf"{re.escape(prefix)}-{p_num:03d}[a-z]?[_]?", re.IGNORECASE)
            
            found = False
            for f in files:
                if pattern.search(f):
                    found = True
                    break
                    
            if not found:
                total_missing += 1
                total_missing += 0 # Keep tracking clean
                missing_by_prompt[p_num] = missing_by_prompt.get(p_num, []) + [prod_name]
                missing_by_product[prod_name] = missing_by_product.get(prod_name, []) + [p_num]

    print("--------------------------------------------------")
    print(f"📊 Scan results:")
    print(f"   • Total render copies checked: {total_expected}")
    print(f"   • Missing (deleted) renders: {total_missing}")
    print("--------------------------------------------------")
    
    if total_missing == 0:
        print("🎉 Zero missing renders! All expected images exist in your OneDrive folders.")
        # Clear rerun prompts file
        if os.path.exists(RERUN_PROMPTS_PATH):
            os.remove(RERUN_PROMPTS_PATH)
        return
        
    # Generate rerun prompts list
    rerun_prompts = []
    print("\n📝 Compiling rerun prompt list...")
    
    for p_num in sorted(missing_by_prompt.keys()):
        # Get the actual prompt row from rooms_turboflow_batch2
        room_data = rooms[p_num - 1]
        prompt_text = room_data.get("prompt")
        
        # Add to our list
        rerun_prompts.append(prompt_text)
        
    # Write new prompt file
    with open(RERUN_PROMPTS_PATH, "w", encoding="utf-8", newline="\n") as f:
        for rp in rerun_prompts:
            f.write(rp + "\n")
            
    print(f"✅ Generated rerun prompts file: {RERUN_PROMPTS_PATH}")
    print(f"   Contains exactly {len(rerun_prompts)} prompts to copy-paste into TurboFlow.")
    
    # Write Markdown Report
    print("📝 Generating markdown report...")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# 📋 Batch 2 Quality Review & Rerun Plan\n\n")
        f.write("Ditt bibliotek har skannats framgångsrikt efter att du har tagit bort de bilder som inte höll måttet. ")
        f.write("Här är din sammanställning och plan för att göra om dem!\n\n")
        
        f.write("## 📊 Sammanfattning\n")
        f.write(f"- 📸 **Totalt förväntade bildkopior**: {total_expected}\n")
        f.write(f"- ❌ **Borttagna (underkända) bilder**: {total_missing}\n")
        f.write(f"- 🔄 **Prompter som måste köras om**: {len(rerun_prompts)} st (av 220)\n\n")
        
        f.write("## 📂 Skadade/Borttagna bilder per möbel\n")
        f.write("Följande möbler saknar en eller flera renderingar för att de har tagits bort under granskningen:\n\n")
        f.write("| Möbel / Produkt | Saknade prompt-rader | Antal saknade |\n")
        f.write("| :--- | :--- | :--- |\n")
        for prod_name, p_nums in sorted(missing_by_product.items()):
            p_nums_str = ", ".join(f"`{p:03d}`" for p in sorted(p_nums))
            f.write(f"| {prod_name} | {p_nums_str} | {len(p_nums)} st |\n")
            
        f.write("\n## 🔄 Rerun-instruktioner\n")
        f.write("1. Öppna TurboFlow-tillägget i Chrome.\n")
        f.write("2. Klicka på **Clear** i promptfältet för att rensa gamla prompter.\n")
        f.write("3. Öppna filen **[rerun_prompts_batch2.txt](file:///C:/Users/AndronikLindgren/.gemini/antigravity/scratch/reforma-turboflow/rerun_prompts_batch2.txt)**, kopiera all text och klistra in i promptfältet.\n")
        f.write("4. Eftersom bilderna redan är taggade i ditt bibliotek med `@ID` så kommer TurboFlow att mappa dem automatiskt!\n")
        f.write("5. Klicka på **Generate Batch** för att generera om de saknade bilderna loss.\n")
        
    print(f"✅ Generated detailed Markdown Report: {REPORT_PATH}")
    print("==================================================")

if __name__ == "__main__":
    main()
