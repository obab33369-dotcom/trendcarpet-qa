import os
import json
import base64
import requests
import math
import re
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

V3_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v4\artiklar"
GRID_OUT_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\qa_grids"
ENV_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
REPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\bad_crops_report.json"
EXCLUSIONS_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\qa_exclusions.json"

def load_gemini_key():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

def build_grid_image(images_list, start_idx, chunk_size=25, cols=5):
    rows = math.ceil(chunk_size / cols)
    cell_w, cell_h = 300, 300
    grid_w = cols * cell_w
    grid_h = rows * cell_h
    
    # Create white canvas
    grid_img = Image.new("RGB", (grid_w, grid_h), "white")
    draw = ImageDraw.Draw(grid_img)
    
    # Try loading font
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 12)
        except OSError:
            font = ImageFont.load_default()
            
    for i in range(chunk_size):
        idx = start_idx + i
        if idx >= len(images_list):
            break
            
        filename = images_list[idx]
        img_path = os.path.join(V3_DIR, filename)
        
        c = i % cols
        r = i // cols
        x0 = c * cell_w
        y0 = r * cell_h
        
        # Draw cell border
        draw.rectangle([x0, y0, x0 + cell_w - 1, y0 + cell_h - 1], outline=(220, 220, 220))
        
        try:
            with Image.open(img_path) as img:
                # Resize image to fit in 280x230 box
                max_w, max_h = 280, 230
                img_w, img_h = img.size
                
                ratio = min(max_w / img_w, max_h / img_h)
                new_w = int(img_w * ratio)
                new_h = int(img_h * ratio)
                
                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.ANTIALIAS
                    
                resized_img = img.resize((new_w, new_h), resample)
                
                # Center image inside the 300x240 upper cell box
                offset_x = x0 + (cell_w - new_w) // 2
                offset_y = y0 + (240 - new_h) // 2
                
                grid_img.paste(resized_img, (offset_x, offset_y))
        except Exception as e:
            draw.text((x0 + 10, y0 + 100), f"Error loading image:\n{e}", fill="red", font=font)
            
        # Draw filename text at the bottom 60px of the cell
        text = filename
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            try:
                text_w, text_h = font.getsize(text)
            except AttributeError:
                text_w, text_h = 120, 12
                
        tx = x0 + (cell_w - text_w) // 2
        ty = y0 + 240 + (60 - text_h) // 2
        draw.text((tx, ty), text, fill="black", font=font)
        
    return grid_img

def analyze_grid_with_gemini(grid_img, key, grid_num):
    buffered = BytesIO()
    grid_img.convert('RGB').save(buffered, format="JPEG", quality=85)
    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Du är en kvalitetskontrollör för en möbelaffär online. Analysera detta rutnät (grid) med produktbilder. "
        "Under varje bild står dess filnamn. Vi behöver identifiera alla produktbilder som är FELAKTIGT BESKURNA "
        "eller skadade. "
        "\n\nKriterier för felaktig beskärning (bad crop):"
        "\n1. Delar av möbeln är avskuren vid bildkanterna (t.ex. bara stolsbenen syns, bara ryggstödet syns, eller sidorna är kapade)."
        "\n2. Produkten är extremt liten eller malplacerad jämfört med övriga bilder i rutnätet."
        "\n3. Bilden visar en närbild/zoom på trä, tyg eller en detalj snarare än hela möbeln (eftersom detta är huvudkatalogen 'artiklar' ska hela produkten synas)."
        "\n\nNotera: Om möbeln syns helt och hållet och är centrerad och proportionerlig, så är den KORREKT. Vi letar ENBART efter felaktiga beskärningar."
        "\n\nSvara strikt i följande JSON-format:"
        "\n{"
        "\n  \"bad_images\": ["
        "\n    {"
        "\n      \"filename\": \"filnamn.jpg\","
        "\n      \"reason\": \"Beskrivning av felet, t.ex. 'Endast stolsben synliga' eller 'Bordsskivan avskuren'\""
        "\n    }"
        "\n  ]"
        "\n}"
    )
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    print(f"Skickar rutnät {grid_num} till Gemini...")
    res = requests.post(url, headers=headers, json=data, timeout=45)
    if res.status_code == 200:
        try:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            return json.loads(text_resp)
        except Exception as e:
            print(f"Fel vid parsning av svar för rutnät {grid_num}: {e}")
            print("Rått svar från Gemini:", res.text)
            return {"bad_images": []}
    else:
        print(f"Fel från Gemini API (kod {res.status_code}): {res.text}")
        return {"bad_images": []}

def clean_digits(s):
    return "".join(re.findall(r'\d+', s))

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def fuzzy_match_filename(flagged_fn, all_files):
    flagged_lower = flagged_fn.lower()
    
    # 1. Exact match (case-insensitive)
    for f in all_files:
        if f.lower() == flagged_lower:
            return f
            
    # 2. Match after cleaning digits (OCR typo correction)
    flagged_digits = clean_digits(flagged_lower)
    if not flagged_digits:
        return None
        
    best_match = None
    best_dist = 9999
    
    for f in all_files:
        f_lower = f.lower()
        f_digits = clean_digits(f_lower)
        if not f_digits:
            continue
            
        if flagged_digits == f_digits:
            return f
            
        dist = levenshtein_distance(flagged_digits, f_digits)
        if dist < best_dist:
            best_dist = dist
            best_match = f
            
    # Max distance of 2 allowed for OCR digits mismatches
    if best_dist <= 2:
        return best_match
        
    return None

def query_individual_image(img_path, key):
    try:
        with Image.open(img_path) as img:
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Kunde inte läsa/processa bild {img_path}: {e}")
        return {"classification": "ERROR", "reason": f"Läsfel: {e}"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "Look at this product image. Is the main furniture item physically cut off/cropped at the edges of the image? "
        "For example, are the legs cut off at the bottom, or is the top/sides cut off?\n"
        "Please classify it as one of the following:\n"
        "1. 'COMPLETE': The product is fully visible and not cut off at all.\n"
        "2. 'CUT_OFF_DETAIL': The product is a detail/close-up view (e.g. showing only the tabletop wood, or a shelf mechanism, or drawer close-up) so it is naturally cropped.\n"
        "3. 'CUT_OFF_BAD': The product is a full shot but got cut off at the edge (e.g. legs are clipped at the very bottom, or the top of the backrest touches/goes past the top edge).\n\n"
        "Answer in JSON format:\n"
        "{\n"
        "  \"classification\": \"COMPLETE\" | \"CUT_OFF_DETAIL\" | \"CUT_OFF_BAD\",\n"
        "  \"reason\": \"Explain why\"\n"
        "}"
    )

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_data}}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            res_json = res.json()
            text_resp = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            return json.loads(text_resp)
        else:
            print(f"API-fel för {os.path.basename(img_path)}: {res.text}")
            return {"classification": "ERROR", "reason": f"API-kod {res.status_code}"}
    except Exception as e:
        print(f"Nätverksfel för {os.path.basename(img_path)}: {e}")
        return {"classification": "ERROR", "reason": str(e)}

def main():
    print("=== STARTAR QUALITY ASSURANCE MED GEMINI ===")
    
    # 1. Load key
    key = load_gemini_key()
    if not key:
        print("Kunde inte ladda GEMINI_API_KEY från miljöfilen!")
        return
    print("Gemini API-nyckel inläst framgångsrikt.")
    
    # 2. Get list of files
    if not os.path.exists(V3_DIR):
        print(f"Hittade inte utdatamappen: {V3_DIR}")
        return
        
    exclusions = set()
    if os.path.exists(EXCLUSIONS_PATH):
        try:
            with open(EXCLUSIONS_PATH, 'r', encoding='utf-8') as ef:
                exclusions_list = json.load(ef)
                exclusions = set(x.lower() for x in exclusions_list)
            print(f"Laddade {len(exclusions)} st bilder att exkludera från QA-rapporten.")
        except Exception as e:
            print(f"Kunde inte ladda exkluderingslistan: {e}")

    all_files = [f for f in os.listdir(V3_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    filtered_all_files = [f for f in all_files if f.lower() not in exclusions]
    filtered_all_files.sort()
    print(f"Hittade totalt {len(filtered_all_files)} produktbilder att granska.")
    
    # Create grid output dir
    os.makedirs(GRID_OUT_DIR, exist_ok=True)
    
    chunk_size = 25
    total_grids = math.ceil(len(filtered_all_files) / chunk_size)
    print(f"Genererar {total_grids} st rutnät (grids)...")
    
    raw_bad_images = []
    
    for g in range(total_grids):
        start_idx = g * chunk_size
        current_chunk_size = min(chunk_size, len(filtered_all_files) - start_idx)
        print(f"Skapar rutnät {g+1}/{total_grids} (index {start_idx} till {start_idx + current_chunk_size - 1})...")
        
        # Build grid image
        grid_img = build_grid_image(filtered_all_files, start_idx, current_chunk_size, cols=5)
        
        # Save grid image for manual reference
        grid_save_path = os.path.join(GRID_OUT_DIR, f"grid_{g+1}.jpg")
        grid_img.save(grid_save_path, "JPEG", quality=85)
        print(f"  Rutnät sparat till: {grid_save_path}")
        
        # Call Gemini
        result = analyze_grid_with_gemini(grid_img, key, g+1)
        bad_in_grid = result.get("bad_images", [])
        print(f"  Gemini hittade {len(bad_in_grid)} flaggade bilder i detta rutnät.")
        for item in bad_in_grid:
            print(f"    - Flaggad fil: {item.get('filename')}: {item.get('reason')}")
            raw_bad_images.append(item)
            
    # 3. Perform individual validation on flagged images
    print("\n=== PÅBÖRJAR INDIVIDUELL QA-VERIFIERING PÅ FLAGGADE BILDER ===")
    bad_images_report = []
    newly_excluded = []
    
    for item in raw_bad_images:
        flagged_fn = item.get("filename")
        if not flagged_fn:
            continue
            
        matched_fn = fuzzy_match_filename(flagged_fn, all_files)
        if not matched_fn:
            print(f"  [OCR-SPÖKE] Flaggan '{flagged_fn}' kunde inte matchas till någon befintlig fil. Hoppar över.")
            continue
            
        # If it matched a file that's already in exclusions, skip it
        if matched_fn.lower() in exclusions:
            print(f"  [EXKLUDERAD] '{matched_fn}' är redan exkluderad. Hoppar över.")
            continue
            
        img_path = os.path.join(V3_DIR, matched_fn)
        print(f"  Verifierar enskild bild '{matched_fn}' (matchad från '{flagged_fn}')...")
        
        res = query_individual_image(img_path, key)
        classification = res.get("classification", "ERROR")
        reason = res.get("reason", "Ingen anledning angiven")
        
        print(f"    - Klassificering: {classification} | Anledning: {reason}")
        
        if classification in ["COMPLETE", "CUT_OFF_DETAIL"]:
            print(f"    -> [FALSK POSITIV] Bilden godkänns. Lägger till '{matched_fn}' i exkluderingslistan.")
            newly_excluded.append(matched_fn)
        elif classification == "CUT_OFF_BAD":
            print(f"    -> [FAKTISKT FEL] Bilden är felaktigt beskuren.")
            bad_images_report.append({
                "filename": matched_fn,
                "reason": f"Individuell granskning: {reason} (Original anledning: {item.get('reason')})"
            })
        else: # ERROR
            print(f"    -> [API FEL] Sparar originalflaggan för säkerhets skull.")
            bad_images_report.append({
                "filename": matched_fn,
                "reason": f"API-fel vid kontroll: {reason} (Original anledning: {item.get('reason')})"
            })
            
    # 4. Save newly excluded images back to qa_exclusions.json
    if newly_excluded:
        try:
            # Read current list
            current_exclusions_list = []
            if os.path.exists(EXCLUSIONS_PATH):
                with open(EXCLUSIONS_PATH, 'r', encoding='utf-8') as ef:
                    current_exclusions_list = json.load(ef)
            
            # Merge and sort
            merged_exclusions = list(set(current_exclusions_list + newly_excluded))
            merged_exclusions.sort()
            
            with open(EXCLUSIONS_PATH, 'w', encoding='utf-8') as ef:
                json.dump(merged_exclusions, ef, indent=2, ensure_ascii=False)
            print(f"\nSparade {len(newly_excluded)} st nya falska positiva i '{EXCLUSIONS_PATH}'. Totalt exkluderade: {len(merged_exclusions)}.")
        except Exception as e:
            print(f"\nKunde inte uppdatera exkluderingslistan: {e}")
            
    # 5. Save final bad crops report
    try:
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(bad_images_report, f, indent=2, ensure_ascii=False)
        print(f"\nSlutrapport sparad till: {REPORT_PATH}")
    except Exception as e:
        print(f"\nKunde inte spara slutrapporten: {e}")
        
    print(f"\n=== QA GRANSKNING KLAR ===")
    print(f"Totalt antal faktiska fel upptäckta: {len(bad_images_report)}")
    if bad_images_report:
        print("\nLista över bekräftade fel:")
        for item in bad_images_report:
            print(f" - {item.get('filename')}: {item.get('reason')}")

if __name__ == "__main__":
    main()
