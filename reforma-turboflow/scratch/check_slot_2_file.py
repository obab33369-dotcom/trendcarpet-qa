import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")

def extract_slot_from_filename(filename):
    fn_lower = filename.lower()
    m_double_wonder = re.search(r'-(\d+)-(\d+)-wonder', fn_lower)
    if m_double_wonder:
        return int(m_double_wonder.group(2))
    m_double_w_wonder = re.search(r'-(\d+)-(\d+)-w-wonder', fn_lower)
    if m_double_w_wonder:
        return int(m_double_w_wonder.group(2))
    m_w_wonder = re.search(r'-(\d+)-w-wonder', fn_lower)
    if m_w_wonder:
        return int(m_w_wonder.group(1))
    m_wonder_w = re.search(r'-(\d+)-wonder-w', fn_lower)
    if m_wonder_w:
        return int(m_wonder_w.group(1))
    m_w = re.search(r'-(\d+)-w', fn_lower)
    if m_w:
        return int(m_w.group(1))
    m_digit = re.search(r'[-_](\d+)\.[a-z]+$', fn_lower)
    if m_digit:
        return int(m_digit.group(1))
    return None

def is_processed_render(filename):
    fn_lower = filename.lower()
    has_double_index = re.search(r'-(\d+)-(\d+)-?w?', fn_lower) is not None
    has_wonder = 'wonder' in fn_lower
    if fn_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
        if has_wonder:
            return True
        if not has_double_index:
            if '-w-' in fn_lower or '-w.' in fn_lower or fn_lower.endswith(('-w.jpg', '-w.jpeg')):
                return True
    return False

# Scan the folder
dir_path = os.path.join(NEW_WHITE_BG_DIR, "armchairs", "Fåtölj _Gori_ - VitTeddy")
files = os.listdir(dir_path)
processed_renders = [f for f in files if is_processed_render(f)]

slots_candidates = {}
for f in processed_renders:
    slot = extract_slot_from_filename(f)
    if slot is not None:
        if slot not in slots_candidates:
            slots_candidates[slot] = []
        slots_candidates[slot].append(f)

print("Slots Candidates:")
for slot, cands in sorted(slots_candidates.items()):
    print(f"Slot {slot}:")
    for cand in cands:
        cand_lower = cand.lower()
        score = 0
        if cand_lower.endswith(('.jpg', '.jpeg')) and ('-w-' in cand_lower or '-w.' in cand_lower or cand_lower.endswith(('-w.jpg', '-w.jpeg', '-w-wonder.jpg', '-w-wonder.jpeg', '-wonder-w.jpg', '-wonder-w.jpeg'))):
            score = 10
        elif cand_lower.endswith('.webp'):
            score = 5
        elif 'wonder' in cand_lower:
            score = 4
        print(f"  {cand} -> score={score}")
