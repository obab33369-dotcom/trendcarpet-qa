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

ORIG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
unmapped = [
    "Stol _Ängom_ - Ljusbeige",
    "21 Stol _Montmartre_ - Vintage svart (ảnh web)",
    "28 Stol _Montmartre_ - Vintage svart_antik (ảnh web)",
    "43 Stol _Midnatt_ - Sammet (ảnh web",
    "44 Stol _Montmartre_ - Vintage Koppar (ảnh web)",
    "49 Stol _Montmartre_ - Vit lackad",
    "51 Stol Vintage - Läder_Järn (ảnh web",
    "52 Stol _Montmartre_ - Röd lackad (ảnh web)",
    "54 Stol _Montmartre_ - Rustik stål (ảnh web)",
    "55 Stol _Montmartre_ - Gul lackad (ảnh web)",
    "59 Stol _Montmartre_ - Svart lack (ảnh web)",
    "60 Stol _Montmartre_ - Orange lack (ảnh web)",
    "Adventsstjärna _Oslo_ 60cm - Vit",
    "Sofa bed _San Francisco_ - Dark grey",
    "Sofa bed _Texas_ - Dark grey",
    "Sofa bed _Texas_ - Light grey",
    "Vägghylla _Hydra_ 114cm - SvartNatur",
    "Vägghylla _Hydra_ 24cm - SvartNatur"
]

def clean_for_print(s):
    return s.encode('ascii', errors='replace').decode('ascii')

orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]

print("--- SEARCH RESULTS ---")
for u_name in unmapped:
    print(f"\nUnmapped: '{clean_for_print(u_name)}'")
    # Extract keywords
    clean_words = re.sub(r'^\d+\s*', '', u_name)
    clean_words = re.sub(r'\(.*?\)', '', clean_words)
    clean_words = clean_words.replace('_', ' ').replace('-', ' ').lower()
    
    # Replace Swedish characters to ensure match
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u'}
    for char, rep in repl.items():
        clean_words = clean_words.replace(char, rep)
        
    words = [w for w in clean_words.split() if len(w) > 2 and w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', 'pack', 'byra', 'skap', 'skank', 'hylla', 'bank', 'sits', 'bed', 'anh', 'web', 'vagg', 'vagghylla', 'stjarna', 'adventsstjarna', 'lack', 'lackad')]
    
    # Try search by words
    matches = []
    for o_folder in orig_folders:
        o_lower = o_folder.lower()
        # Normalise original folder as well
        for char, rep in repl.items():
            o_lower = o_lower.replace(char, rep)
            
        # count how many words match
        match_count = sum(1 for w in words if w in o_lower)
        if match_count > 0:
            matches.append((match_count, o_folder))
            
    matches.sort(reverse=True, key=lambda x: (x[0], x[1]))
    for score, o_folder in matches[:8]:
        print(f"  [{score}] -> {clean_for_print(o_folder)}")
