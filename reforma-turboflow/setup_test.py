import os
import shutil
import re

SOURCE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
TARGET_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_furniture"

def main():
    print("Setting up test directory (balanced)...")
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory {SOURCE_DIR} does not exist!")
        return
        
    files = os.listdir(SOURCE_DIR)
    valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
    
    # Clean target folder first to ensure only our balanced set remains
    for f in os.listdir(TARGET_DIR):
        try:
            os.remove(os.path.join(TARGET_DIR, f))
        except Exception:
            pass
            
    product_images = {}
    for f in files:
        if f.lower().endswith(valid_exts):
            # Parse product name
            base, _ = os.path.splitext(f)
            base = re.sub(r'^\d+_', '', base)
            base = re.sub(r'-\d+-\w+-wonder$', '', base)
            base = re.sub(r'-\d+$', '', base)
            
            if base not in product_images:
                product_images[base] = []
            product_images[base].append(f)
            
    print(f"Total unique products found: {len(product_images)}")
    
    # We want a balanced set of categories:
    # 1. Bord (matbord, skrivbord, soffbord, sidobord, avlastningsbord)
    # 2. Stolar (stol, pinnstol, karmstol, pall, barstol, loungestol, matsalsstol)
    # 3. Matta (matta, carpet, rug)
    # 4. Förvaring (byrå, tv-bänk, bokhylla, skänk, skåp, vägghylla, hylla, sideboard)
    
    categories = {
        "bord": [],
        "stol": [],
        "matta": [],
        "förvaring": []
    }
    
    for prod_name, img_list in sorted(product_images.items()):
        img_list.sort() # Ensure first image is first
        primary_img = img_list[0]
        
        name_lower = prod_name.lower()
        
        # Categorize
        is_classified = False
        if any(k in name_lower for k in ["matta", "carpet", "rug"]):
            categories["matta"].append(primary_img)
            is_classified = True
        elif any(k in name_lower for k in ["matbord", "skrivbord", "soffbord", "sidobord", "avlastningsbord", "klaffbord", "barbord", "bord"]):
            # Sängbord is usually classified under storage or small table. Let's make it bord or storage.
            if "sängbord" in name_lower:
                categories["förvaring"].append(primary_img)
            else:
                categories["bord"].append(primary_img)
            is_classified = True
        elif any(k in name_lower for k in ["stol", "pall", "barstol", "pinnstol", "karmstol", "loungestol", "matsalsstol", "puff", "sittpuff", "fåtölj", "gungstol"]):
            categories["stol"].append(primary_img)
            is_classified = True
        elif any(k in name_lower for k in ["byrå", "tv-bänk", "hylla", "bokhylla", "skänk", "skåp", "vägghylla", "vägghyllor", "sideboard", "skänk", "sängbord", "klädskåp", "skoskåp"]):
            categories["förvaring"].append(primary_img)
            is_classified = True
            
    print("Found in dataset:")
    for cat_name, items in categories.items():
        print(f"  - {cat_name}: {len(items)} products available")
        
    # We will pick a balanced set up to 100 total
    # Let's take up to 25 items from each of the 4 main categories
    selected_files = []
    category_counts = {}
    
    for cat_name, items in categories.items():
        # Select up to 25 items for each category
        chosen = items[:25]
        selected_files.extend(chosen)
        category_counts[cat_name] = len(chosen)
        
    print(f"Selected {len(selected_files)} balanced primary images for the test batch:")
    for cat, count in category_counts.items():
        print(f"  - {cat}: {count}")
        
    # Copy files
    copied_count = 0
    for f in selected_files:
        src = os.path.join(SOURCE_DIR, f)
        dst = os.path.join(TARGET_DIR, f)
        shutil.copyfile(src, dst)
        copied_count += 1
        
    print(f"Successfully copied {copied_count} balanced primary images to {TARGET_DIR}")

if __name__ == "__main__":
    main()
