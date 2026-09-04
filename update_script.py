import re

with open(r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\vision_auto_corrector.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace CATEGORY_TARGETS and classify_and_size_product and adjust_size_by_name
pattern1 = r"# Category Specifications \(Targets\).*?def is_white_background_robust"
repl1 = r"""# Category Specifications (Targets)
# format: (target_w_fill, target_h_fill, floor_pct, is_centered)
CATEGORY_TARGETS = {
    "sofa_2_seat": (0.88, 0.52, 0.13, False),
    "sofa_3_seat": (0.94, 0.46, 0.13, False),
    "bench_hallway": (0.88, 0.48, 0.10, False),
    "armchair": (0.85, 0.78, 0.10, False),
    "chair_dining": (0.70, 0.85, 0.10, False),
    "barstool": (0.55, 0.88, 0.10, False),
    "stool": (0.52, 0.52, 0.10, False),
    "table_dining": (0.92, 0.52, 0.11, False),
    "table_coffee": (0.84, 0.50, 0.11, False),
    "table_bedside": (0.58, 0.68, 0.10, False),
    "desk": (0.86, 0.68, 0.11, False),
    "sideboard_credenza": (0.92, 0.65, 0.10, False),
    "chest_of_drawers": (0.76, 0.82, 0.10, False),
    "cabinet_large": (0.82, 0.90, 0.10, False),
    "bookshelf_floor": (0.80, 0.90, 0.10, False),
    "shelf_hanging": (0.81, 0.40, 0.50, True),
    "lamp_floor": (0.48, 0.92, 0.10, False),
    "lamp_table": (0.42, 0.68, 0.50, True),
    "lamp_pendant": (0.72, 0.68, 0.50, True),
    "lamp_wall": (0.58, 0.58, 0.50, True),
    "default": (0.85, 0.85, 0.50, True)
}

CATEGORY_GUIDELINES = {
    "sofa_2_seat": "The sofa should be wide, filling about 88% of the width, and centered. It should look balanced and not too small.",
    "sofa_3_seat": "The sofa should be very wide, filling about 94% of the width, and centered. It should look balanced and not too small.",
    "bench_hallway": "The bench should be wide and low, standing on the floor line. It is normal for it to have a lot of white space at the top since it is a low object.",
    "chair_dining": "The dining chair is a tall and narrow object. It should occupy about 85% of the height and stand on the floor line. It is normal for it to have empty space on the sides (occupying about 70% width).",
    "armchair": "The armchair should occupy about 85% width and 78% height, standing on the floor.",
    "barstool": "The barstool is very tall and narrow. It should occupy about 88% of the height and stand on the floor line. It is normal for it to have significant empty space on the sides (occupying about 55% width).",
    "stool": "The stool is small and square. It should stand on the floor line and occupy about 52% of the width and height, centered horizontally.",
    "table_dining": "The table should be wide, filling about 92% of the width, and stand on the floor line. It should look balanced and not too small.",
    "table_coffee": "The coffee table is wide and low. It should stand on the floor line and occupy about 84% of the width. It is normal for it to have a lot of white space at the top since it is a low object.",
    "table_bedside": "The bedside table is small and square-ish. It should stand on the floor line and occupy about 58% of the width and 68% of the height.",
    "desk": "The desk or console table should stand on the floor line and occupy about 86% of the width and 68% of the height.",
    "sideboard_credenza": "The sideboard or tv bench is wide and medium-low. It should stand on the floor line and occupy about 92% of the width.",
    "chest_of_drawers": "The chest of drawers (byrå) should stand on the floor line and occupy about 76% of the width and 82% of the height.",
    "cabinet_large": "The large cabinet or wardrobe should stand on the floor line and occupy about 82% of the width and 90% of the height.",
    "bookshelf_floor": "The floor bookshelf should stand on the floor line and occupy about 80% of the width and 90% of the height.",
    "shelf_hanging": "The hanging shelf should be centered vertically and horizontally, occupying about 81% of the width and 40% of the height.",
    "lamp_floor": "The floor lamp is very tall and narrow. It should stand on the floor line and occupy about 92% of the height. It is normal to have empty space on the sides.",
    "lamp_table": "The table lamp should be centered vertically and horizontally, occupying about 42% of the width and 68% of the height.",
    "lamp_pendant": "The taklampa/pendel should be centered vertically and horizontally, occupying about 72% of the width and 68% of the height.",
    "lamp_wall": "The wall lamp should be centered vertically and horizontally, occupying about 58% of the width and 58% of the height.",
    "default": "The object should be centered and occupy a realistic proportion of the frame, looking balanced."
}

def classify_and_size_product(prod_name):
    name_lower = prod_name.lower()
    if any(x in name_lower for x in ["soffa", "sofa", "baddsoffa", "bäddsoffa", "schaslong", "modulsoffa"]):
        if "soffbord" not in name_lower:
            is_2_seat = any(x in name_lower for x in ["2-sits", "2-seater", "2sits", "2seater", "loveseat", "love-seat", "baddfatolj", "bäddfåtölj"])
            return "sofa_2_seat" if is_2_seat else "sofa_3_seat"
    if any(x in name_lower for x in ["skap", "skåp", "byra", "byrå", "sideboard", "skank", "skänk", "garderob", "tv-bank", "tv-bänk", "tv bank", "tv bänk", "tvbank", "tvbänk", "vinhylla"]):
        if any(x in name_lower for x in ["byra", "byrå"]):
            return "chest_of_drawers"
        elif any(x in name_lower for x in ["sideboard", "skank", "skänk", "tv-bank", "tv-bänk", "tv bank", "tv bänk", "tvbank", "tvbänk"]):
            return "sideboard_credenza"
        elif any(x in name_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ", "högskåp", "hogskap"]):
            return "cabinet_large"
        else:
            if any(x in name_lower for x in ["litet", "sido", "säng"]):
                return "chest_of_drawers"
            return "cabinet_large"
    if any(x in name_lower for x in ["bänk", "bank", "hallbänk", "hallbank", "sittbänk", "sittbank", "dagbädd", "daybed"]):
        return "bench_hallway"
    if any(x in name_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"]):
        if any(x in name_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol"]):
            return "armchair"
        elif "barstol" in name_lower:
            return "barstool"
        elif any(x in name_lower for x in ["pall", "puff", "sittpuff"]):
            return "stool"
        else:
            return "chair_dining"
    if any(x in name_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord"]):
        if any(x in name_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"]):
            return "table_dining"
        elif any(x in name_lower for x in ["soffbord", "soff bord"]):
            return "table_coffee"
        elif any(x in name_lower for x in ["sangbord", "sängbord", "nattbord"]):
            return "table_bedside"
        elif any(x in name_lower for x in ["skrivbord", "avlastningsbord", "konsolbord", "skriv bord"]):
            return "desk"
        else:
            return "table_coffee"
    if any(x in name_lower for x in ["hylla", "hyllor", "vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "bookcase"]):
        if any(x in name_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"]):
            return "shelf_hanging"
        else:
            return "bookshelf_floor"
    if any(x in name_lower for x in ["lamp", "lampa", "belysning", "ljus", "stjarna", "stjärna", "advent"]):
        if "golv" in name_lower:
            return "lamp_floor"
        elif "bord" in name_lower:
            return "lamp_table"
        elif any(x in name_lower for x in ["taklampa", "pendel", "krona", "plafond", "adventstjarna", "adventstjärna", "stjarna", "stjärna", "oslo", "sally", "lotus"]):
            return "lamp_pendant"
        elif "vagg" in name_lower or "vägg" in name_lower:
            return "lamp_wall"
        else:
            return "lamp_pendant"
    return "default"

def adjust_size_by_name(category, name, target_w, target_h):
    name_clean = re.sub(r'(202[0-9]|26u)', '', name.lower())
    numbers = re.findall(r'\d+', name_clean)
    m_cross = re.search(r'(\d+)\s*x\s*(\d+)', name_clean)
    
    if category == "table_dining":
        length = 180
        if m_cross:
            length = int(m_cross.group(1))
        else:
            for num in map(int, numbers):
                if 100 <= num <= 260:
                    length = num
                    break
        scale = length / 180.0
        target_w = target_w * scale
        target_w = max(0.70, min(0.94, target_w))
    elif category == "shelf_hanging":
        width = 75
        for num in map(int, numbers):
            if 15 <= num <= 150:
                width = num
                break
        scale = width / 75.0
        target_w = target_w * scale
        target_w = max(0.65, min(0.94, target_w))
    elif category == "cabinet_large":
        height = 180
        if m_cross:
            height = int(m_cross.group(2))
        else:
            for num in map(int, numbers):
                if 100 <= num <= 240:
                    height = num
                    break
        scale = height / 180.0
        target_h = target_h * scale
        target_h = max(0.70, min(0.94, target_h))
    return target_w, target_h

def is_white_background_robust"""

content = re.sub(pattern1, lambda m: repl1, content, flags=re.DOTALL)

# 2. Update call_gemini_verification
pattern2 = r'def call_gemini_verification.*?return True, "Defaulted to true due to API error"'
repl2 = r"""def call_gemini_verification(img_path, category, w_expected, h_expected, y_expected_center, is_centered):
    with open(img_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode('utf-8')
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    vertical_desc = f"centered vertically (vertical center around {y_expected_center*100:.1f}%)" if not is_centered else "centered vertically (vertical center at 50.0%)"
    if not is_centered:
        vertical_desc += f" so that its bottom edge is aligned with the floor line (about {(y_expected_center + h_expected/2)*100:.1f}% from the top)"
        
    guideline = CATEGORY_GUIDELINES.get(category, CATEGORY_GUIDELINES["default"])

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"You are a quality assurance assistant for a premium furniture store. Analyze this corrected product image of category '{category}'.\n"
                            f"Guidelines for this category:\n{guideline}\n\n"
                            f"The furniture object should be:\n"
                            f"- Centered horizontally (horizontal center at 50.0%).\n"
                            f"- {vertical_desc}.\n"
                            f"- Occupying approximately {w_expected*100:.1f}% width and {h_expected*100:.1f}% height of the frame (tolerance +/- 5%).\n"
                            f"- Not cut off or cropped unnaturally.\n"
                            "Verify if the image composition is high-quality, centered, and meets these standards.\n"
                            "Ignore floor shadows and reflections.\n"
                            "Return a JSON object: {\"verified\": true/false, \"reason\": \"...\"}"
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    for attempt in range(3):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=25)
            if res.status_code == 200:
                resp_json = res.json()
                text = resp_json['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(text.strip())
                if "verified" in parsed:
                    return parsed["verified"], parsed.get("reason", "")
            elif res.status_code == 429:
                time.sleep(5)
        except Exception:
            pass
        time.sleep(2)
    return True, "Defaulted to true due to API error\""""

content = re.sub(pattern2, lambda m: repl2, content, flags=re.DOTALL)

# 3. Update is_ok logic in Phase 1
pattern3 = r"""        w_dev = abs\(w_curr - target_w\)
        h_dev = abs\(h_curr - target_h\)
        cx_dev = abs\(cx_curr - 0\.50\)
        
        if not is_centered:
            target_bottom = 1\.0 - floor_pct
            bottom_dev = abs\(ymax - target_bottom\)
        else:
            bottom_dev = abs\(cy_curr - 0\.50\)
            
        tolerance = 0\.03
        is_ok = \(w_curr <= target_w \+ tolerance\) and \(h_curr <= target_h \+ tolerance\) and \\
                \(cx_dev <= tolerance\) and \(bottom_dev <= tolerance\)"""

repl3 = r"""        scale_needed = min(target_w / w_curr, target_h / h_curr)
        cx_dev = abs(cx_curr - 0.50)
        
        if not is_centered:
            target_bottom = 1.0 - floor_pct
            bottom_dev = abs(ymax - target_bottom)
        else:
            bottom_dev = abs(cy_curr - 0.50)
            
        tolerance = 0.05
        is_ok = (0.95 <= scale_needed <= 1.05) and (cx_dev <= tolerance) and (bottom_dev <= tolerance)"""

content = re.sub(pattern3, lambda m: repl3, content)

# 4. Update is_ok logic in Phase 2
pattern4 = r"""        w_dev = abs\(w_curr - target_w\)
        h_dev = abs\(h_curr - target_h\)
        cx_dev = abs\(cx_curr - 0\.50\)
        
        if not is_centered:
            target_bottom = 1\.0 - floor_pct
            bottom_dev = abs\(ymax - target_bottom\)
        else:
            bottom_dev = abs\(cy_curr - 0\.50\)
            
        tolerance = 0\.05
        is_ok = \(w_curr <= target_w \+ tolerance\) and \(h_curr <= target_h \+ tolerance\) and \\
                \(cx_dev <= tolerance\) and \(bottom_dev <= tolerance\)"""

content = re.sub(pattern4, lambda m: repl3, content)

# 5. Fix call_gemini_vision parameter in Phase 2
content = content.replace("bbox = call_gemini_vision(img_path)", "bbox = call_gemini_vision(img_path, category, prod_name)")

with open(r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\vision_auto_corrector.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updates applied successfully.")
