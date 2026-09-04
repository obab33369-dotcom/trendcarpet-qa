import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped")

hardcoded_sku_map = {
    'baddsoffasanfranciscodarkgrey': 'MLM-502390-Darkgrey',
    'baddsoffatexasdarkgrey': 'MLM-502580',
    'baddsoffatexaslightgrey': 'MLM-502580-lightgrey',
    'adventsstjarnaoslo60cmvit': 'WW-advent-star-white-2',
    'stolmontmartrevintagesvart': 'SM-1027C-sblack',
    'stolmontmartrevintagesvartantik': 'SM-1027C-sBlackgold',
    'stolmontmartrevintagekoppar': 'SM-1027C-scopper',
    'stolmontmartrevitlackad': 'SM-1027C-white',
    'stolmontmartrerodlackad': 'SM-1027C-red',
    'stolmontmartrerustikstal': 'SM-1027C-steel',
    'stolmontmartregullackad': 'SM-1027C-yellow',
    'stolmontmartresvartlack': 'SM-1027C-Black',
    'stolmontmartreorangelack': 'SM-1027C-orange',
    'stolvintageladerjarn': 'MA0215',
    'stolvintageladerjarnnhweb': 'MA0215',
    'vagghyllahydra24cmsvartnatur': '79420',
    'vagghyllahydra114cmsvartnatur': '75966',
    'stolmidnattsammet': 'SC-264F',
    'stolmidnattsammetnhweb': 'SC-264F',
}

hardcoded_map = {
    'barstoltarnsjsvart': 'barstoltarnsjobrun',
    'barstoltarnsjovalnot': 'barstoltarnsjosvart',
    'stolgalsvart': 'stolgalgrasvart',
    'karmstolrottingsvart': 'karmstolrottingblack',
    'stolaltabeigevitpigmenterad': 'stolaltavitpigmenterad',
    'modulmessina118x110cmvit': 'modulmessina118x110cmbenvit',
    'soffabaddkapverdekapverdebeige': 'baddsoffakapverdebeige',
    'soffabaddklippanbeige': 'baddsoffaklippanbeige',
    'soffabaddsanfranciscodarkgrey': 'baddfatoljsanfranciscomorkgra',
    'soffabaddtexasdarkgrey': 'baddsoffatexasmorkgra',
    'soffabaddtexaslightgrey': 'baddsoffatexasljusgra',
    'soffabaddtexasbeige': 'baddsoffatexasbeige',
    'matbordfager135cmnatur': 'matbordelsa135cmvitpigmenterad',
    'soffbordtwin2delarnatur': 'soffbordtwinx2natursvart',
    'soffbordruntnagano2delarek': 'soffbordruntnagano2setek',
    'matbordmodena180220x90cmbrun': 'matbordmodena180cmbrun',
    'sidobordsapri45x60cmvalnottravertin': 'sidobordsangbordsapri45x60cmvalnottravertin',
    'soffbordcremerunt75cmvalnot': 'soffbordcremerund75cmvalnot',
    'soffbordcremerunt75cmvitpigmenterad': 'soffbordcremerund75cmvitpigmenterad',
    'soffbordprimes2delarvalnot': 'soffbordprimesvalnot',
    'soffbordcremerunt55cmvitpigmenterad': 'soffbordcremerund55cmvitpigmenterad',
    'line180x90': 'matbordline180x90cmvitpigmenterad',
    'saba120x165': 'matbordsabaovaltrunt120165x120cmek',
    'saba180x90': 'matbordsaba180x90cmek',
    'sidobordtorekovvalnot': 'sidobordtorekovljusvalnot',
    'soffbordnagano2delarek': 'soffbordnagano2setek',
    'sideboardhagaviksvart': 'sideboardhagavik2sektionersvartmassing',
    'tvbankmyshultlnatur': 'tvbankmyshult200x55cmnatur',
    'tvbankmyshultsnatur': 'tvbankmyshult160x55cmnatur',
    'stolangomljusbeige': 'stolangombeige',
}

def normalize_name(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'^\d+\s*', '', text)
    text = text.replace('sofa bed', 'baddsoffa')
    text = text.replace('bed sofa', 'baddsoffa')
    text = text.replace('bed armchair', 'baddfatolj')
    text = text.replace('sofabed', 'baddsoffa')
    text = text.replace('bedsofa', 'baddsoffa')
    text = text.replace('bedarmchair', 'baddfatolj')
    text = text.replace('seater sofa', 'sitssoffa')
    text = text.replace('seatersofa', 'sitssoffa')
    text = text.replace('sofa', 'soffa')
    text = text.replace('module', 'modul')
    text = text.replace('eucalyptus', 'eukalyptus')
    text = text.replace('cape verde', 'kap verde')
    text = text.replace('3-seater', '3-sits')
    text = text.replace('2-seater', '2-sits')
    text = text.replace('3 seater', '3 sits')
    text = text.replace('2 seater', '2 sits')
    text = text.replace('off-white', 'vit')
    text = text.replace('off white', 'vit')
    text = text.replace('offwhite', 'vit')
    text = text.replace('mintgron', 'gron')
    text = text.replace('ongom', 'angom')
    text = text.replace('ängom', 'angom')
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def is_excluded(cat_name, folder_name):
    cat_lower = cat_name.lower()
    folder_lower = folder_name.lower()
    if "armchair" in cat_lower:
        return True
    if any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "pall", "barstol"]):
        return True
    return False

def main():
    print("=== Excluded Products Staging Cleanup ===")
    
    categories = [d for d in os.listdir(NEW_WHITE_BG_DIR) if os.path.isdir(os.path.join(NEW_WHITE_BG_DIR, d))]
    render_folders = []
    for cat in categories:
        cat_path = os.path.join(NEW_WHITE_BG_DIR, cat)
        if cat.lower() == "cabinet":
            nested_path = os.path.join(cat_path, "White background")
            if os.path.exists(nested_path) and os.path.isdir(nested_path):
                cat_path = nested_path
        prods = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
        for p in prods:
            render_folders.append((cat, p))
            
    orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]
    
    # Identify armchairs, stools, and barstools and get their SKUs
    excluded_skus = []
    
    for cat, r_folder in render_folders:
        if is_excluded(cat, r_folder):
            r_norm = normalize_name(r_folder)
            sku = None
            if r_norm in hardcoded_sku_map:
                sku = hardcoded_sku_map[r_norm]
            else:
                if r_norm in hardcoded_map:
                    r_norm = hardcoded_map[r_norm]
                
                found_orig = None
                for o_folder in orig_folders:
                    o_norm = normalize_name(o_folder)
                    if r_norm == o_norm:
                        found_orig = o_folder
                        break
                if not found_orig:
                    for o_folder in orig_folders:
                        o_norm = normalize_name(o_folder)
                        if r_norm in o_norm or o_norm in r_norm:
                            found_orig = o_folder
                            break
                if not found_orig:
                    r_words = set(r_folder.lower().replace('_', ' ').replace('-', ' ').split())
                    for o_folder in orig_folders:
                        o_words = set(o_folder.lower().replace('_', ' ').replace('-', ' ').split())
                        sig_r = {w for w in r_words if w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', '3', '2', 'pack', 'byra', 'skap', 'skänk', 'skank', 'hylla', 'bänk')}
                        sig_o = {w for w in o_words if w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', '3', '2', 'pack', 'byra', 'skap', 'skänk', 'skank', 'hylla', 'bänk')}
                        if sig_r and sig_o and sig_r == sig_o:
                            found_orig = o_folder
                            break
                if found_orig:
                    sku_match = re.search(r'\(([^)]+)\)', found_orig)
                    if sku_match:
                        sku = sku_match.group(1).strip()
            
            if sku:
                excluded_skus.append(sku)
                print(f"Excluded: '{r_folder}' -> SKU: '{sku}'")
                
    # Delete corresponding files in staging directory
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    deleted_files_count = 0
    
    print("\nStarting file deletion...")
    for sku in excluded_skus:
        # 1. Normal image
        norm_p = os.path.join(artiklar_dir, f"{sku}.jpg")
        if os.path.exists(norm_p):
            try:
                os.remove(norm_p)
                print(f"  Deleted: {norm_p}")
                deleted_files_count += 1
            except Exception as e:
                print(f"  Error deleting {norm_p}: {e}")
                
        # 2. Liten image
        liten_p = os.path.join(liten_dir, f"{sku}_S.jpg")
        if os.path.exists(liten_p):
            try:
                os.remove(liten_p)
                print(f"  Deleted: {liten_p}")
                deleted_files_count += 1
            except Exception as e:
                print(f"  Error deleting {liten_p}: {e}")
                
        # 3. Zoom images
        if os.path.exists(zoom_dir):
            for filename in os.listdir(zoom_dir):
                if filename.startswith(f"{sku}_") and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    zoom_p = os.path.join(zoom_dir, filename)
                    try:
                        os.remove(zoom_p)
                        print(f"  Deleted: {zoom_p}")
                        deleted_files_count += 1
                    except Exception as e:
                        print(f"  Error deleting {zoom_p}: {e}")
                        
    print(f"\nCleanup complete. Total files deleted: {deleted_files_count}")

if __name__ == "__main__":
    main()
