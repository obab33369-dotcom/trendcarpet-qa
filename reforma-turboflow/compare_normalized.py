import os
import sys
import re

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background-")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

categories = [d for d in os.listdir(WHITE_BG_DIR) if os.path.isdir(os.path.join(WHITE_BG_DIR, d))]
render_folders = []
for cat in categories:
    cat_path = os.path.join(WHITE_BG_DIR, cat)
    prods = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
    for p in prods:
        render_folders.append((cat, p))

orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]

def normalize_name(name):
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    text = name.lower()
    for char, rep in repl.items():
        text = text.replace(char, rep)
        
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'^\d+\s*', '', text)
    text = text.replace('_', ' ').replace('-', ' ')
    
    words = text.split()
    normalized_words = []
    for w in words:
        if w in ('seater', 'seats', 'sits'):
            continue
        if w in ('sofa', 'soffa'):
            normalized_words.append('soffa')
            continue
        if w in ('bed', 'bädd', 'badd'):
            normalized_words.append('badd')
            continue
        if w in ('armchair', 'fåtölj', 'fatolj'):
            normalized_words.append('fatolj')
            continue
        if w in ('chair', 'stol'):
            normalized_words.append('stol')
            continue
        if w in ('table', 'bord'):
            normalized_words.append('bord')
            continue
        if w in ('desk', 'skrivbord'):
            normalized_words.append('skrivbord')
            continue
        if w in ('bedside', 'sängbord', 'sangbord'):
            normalized_words.append('sangbord')
            continue
        if w in ('coffee', 'soffbord'):
            normalized_words.append('soffbord')
            continue
        if w in ('module', 'modul'):
            normalized_words.append('modul')
            continue
        if w in ('cape', 'verde', 'kapverde'):
            normalized_words.append('kapverde')
            continue
        if w in ('eucalyptus', 'eukalyptus'):
            normalized_words.append('eukalyptus')
            continue
        if w in ('offwhite', 'vit'):
            normalized_words.append('vit')
            continue
        if w in ('mintgrön', 'mintgron', 'grön', 'gron'):
            normalized_words.append('gron')
            continue
        if w in ('valnöt', 'valnot'):
            normalized_words.append('valnot')
            continue
        if w in ('ek', 'oak'):
            normalized_words.append('ek')
            continue
        if w in ('mörkgrå', 'morkgra', 'darkgrey', 'darkgray', 'dark'):
            normalized_words.append('morkgra')
            continue
        if w in ('ljusgrå', 'ljusgra', 'lightgrey', 'lightgray', 'light'):
            normalized_words.append('ljusgra')
            continue
        if w in ('grå', 'gra', 'grey', 'gray'):
            normalized_words.append('gra')
            continue
        if w in ('brun', 'brown'):
            normalized_words.append('brun')
            continue
        if w in ('svart', 'black'):
            normalized_words.append('svart')
            continue
        if w in ('beige', 'beigebouclé', 'beigeboucle'):
            normalized_words.append('beige')
            continue
        if w in ('vitbouclé', 'vitboucle', 'teddy', 'vitteddy'):
            normalized_words.append('vit')
            continue
        if w in ('ongom', 'ängom', 'angom'):
            normalized_words.append('angom')
            continue
        normalized_words.append(re.sub(r'[^a-zA-Z0-9]', '', w))
    return "".join(normalized_words)

# List of currently unmatched items
unmatched = [
    'Module _Messina_ 118x110cm - Off-white',
    'Sofa bed _Cape Verde_ - Beige',
    'Sofa bed _Eucalyptus_ - Beige',
    'Sofa bed _Klippan_ - Beige',
    'Sofa bed _San Francisco_ - Dark grey',
    'Sofa bed _Texas_ - Dark grey',
    'Sofa bed _Texas_ - Light grey',
    'Sofa bed _Texas_ -beige',
    '22 Matbord Fager 135cm  Natur',
    '27 Soffbord _Twin_ 2 delar - Natur',
    '28 Soffbord Runt _Nagano_ 2 delar - Ek',
    '34 Matbord _Modena_ 180-220x90cm - Brun',
    '37 Sidobord _Sapri_ 45x60cm - Valnöt_Travertin',
    '40 Soffbord _Créme_ Runt 75cm - Valnöt',
    '41 Soffbord _Créme_ Runt 75cm - Vitpigmenterad',
    '42 Soffbord _Prime_ S 2 delar - Valnöt',
    '51 Soffbord _Créme_ Runt 55 cm - Vitpigmenterad',
    'Line 180x90',
    'saba-120x165',
    'saba-180x90',
    'Sidobord _Torekov_-Valnöt',
    'Skrivbord _Light_ - Valnöt',
    'Soffbord _Nagano_ 2 delar - Ek'
]

print("Comparing normalized strings:")
for u in unmatched:
    print(f"\nRender folder: '{u}' -> Normalized: '{normalize_name(u)}'")
    
    # Try keyword overlap in orig_folders
    u_clean = u.lower().replace('_', ' ').replace('-', ' ')
    u_words = [w for w in u_clean.split() if len(w) > 2]
    # Remove extremely generic words
    u_words = [w for w in u_words if w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', 'pack', 'delar', 'runt')]
    
    for o in orig_folders:
        o_clean = o.lower()
        if any(w in o_clean for w in u_words if w not in ('offwhite', 'bed', 'sofa')):
            print(f"  Candidate: '{o}' -> Normalized: '{normalize_name(o)}'")
