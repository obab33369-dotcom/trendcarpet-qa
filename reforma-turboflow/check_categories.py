import json
from typing import Dict

db_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

# Copy the exact get_item_category function
CAT_KEY = 'typ_av_möbel'
def get_item_category(filename: str, item: Dict) -> str:
    fname = filename.lower()
    cat_meta = item.get("metadata", {}).get(CAT_KEY, "").strip().lower()
    
    if "taklampa" in fname:
        return "pendant_lamp"
    elif "golvlampa" in fname:
        return "floor_lamp"
    elif "bordslampa" in fname or "lampa" in fname:
        return "table_lamp"
    
    if cat_meta == "matta" or "matta" in fname:
        return "rug"
        
    if "skrivbordsstol" in fname:
        return "desk_chair"
        
    if "barstol" in fname or ("bar" in fname and "stol" in fname):
        return "barstool"
    elif "barbord" in fname:
        return "bartable"
        
    if "f\u00e5t\u00f6lj" in fname or "fatolj" in fname:
        return "armchair"
    elif "b\u00e4ddsoffa" in fname or "soffa" in fname:
        return "sofa"
    elif "soffbord" in fname:
        return "coffeetable"
    elif "s\u00e4ngbord" in fname or "sangbord" in fname:
        return "bedside_table"
    elif "skrivbord" in fname:
        return "desk"
    elif "klaffbord" in fname or "matbord" in fname:
        return "dining_table"
    elif "bord" in fname:
        if "avlastningsbord" in fname or "sidobord" in fname or "sideboard" in fname:
            return "sideboard"
        return "dining_table"
        
    if "tv-b\u00e4nk" in fname or "tv-b\u00f6nk" in fname or "mediab\u00e4nk" in fname:
        return "tv_bench"
    elif "b\u00e4nk" in fname or "bank" in fname:
        return "bench"
    elif "bokhylla" in fname:
        return "bookcase"
    elif "byr\u00e5" in fname:
        return "dresser"
    elif "skosk\u00e5p" in fname:
        return "shoe_cabinet"
    elif "sk\u00e5p" in fname or "sk\u00e4nk" in fname or "sideboard" in fname or "sidobord" in fname or "avlastningsbord" in fname:
        return "cabinet"
        
    if cat_meta == "stol" or "stol" in fname or "pinnstol" in fname or "karmstol" in fname:
        return "dining_chair"
        
    if cat_meta == "f\u00f6rvaring" or cat_meta == "frvaring" or "hylla" in fname:
        return "cabinet"
        
    if cat_meta == "stol":
        return "dining_chair"
    elif cat_meta == "bord":
        return "dining_table"
    elif cat_meta == "matta":
        return "rug"
    return "other"

from collections import Counter
cats = Counter()
other_examples = []
for fname, item in db.items():
    cat = get_item_category(fname, item)
    cats[cat] += 1
    if cat == "other":
        other_examples.append(fname)

print("Categories assigned by current script:")
for cat, cnt in cats.items():
    print(f"  {cat}: {cnt}")

print("\nExamples of 'other' items:")
for ex in other_examples[:20]:
    print(f"  {ex}")
