import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def classify_folder(folder_name):
    name_lower = folder_name.lower()
    if "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower:
        return "Mattor"
    elif "stol" in name_lower or "fåtölj" in name_lower or "barstol" in name_lower or "pinnstol" in name_lower:
        return "Stolar / Fåtöljer"
    elif "bord" in name_lower or "soffbord" in name_lower or "matbord" in name_lower or "skrivbord" in name_lower or "sidobord" in name_lower or "sängbord" in name_lower:
        return "Bord (Matbord, soffbord, sidobord, etc.)"
    elif "soffa" in name_lower or "bäddsoffa" in name_lower:
        return "Soffor / Bäddsoffor"
    elif "hylla" in name_lower or "bokhylla" in name_lower or "vägghylla" in name_lower:
        return "Hyllor / Förvaring"
    elif "byrå" in name_lower or "skänk" in name_lower or "tv-bänk" in name_lower:
        return "Byråer / Skänkar / Mediamöbler"
    elif "matgrupp" in name_lower:
        return "Matgrupper"
    else:
        return "Övrigt / Odefinierat"

def main():
    if not os.path.exists(DISCARD_DIR):
        print("Discard dir does not exist.")
        return
        
    counts = {}
    folder_counts = {}
    
    for folder in os.listdir(DISCARD_DIR):
        folder_path = os.path.join(DISCARD_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
            
        category = classify_folder(folder)
        counts[category] = counts.get(category, 0)
        folder_counts[category] = folder_counts.get(category, 0) + 1
        
        # Count files
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                    counts[category] = counts.get(category, 0) + 1
                    
    print("=== SUMMARY OF REMAINING DISCARDED ITEMS ===")
    total_files = sum(counts.values())
    total_folders = sum(folder_counts.values())
    print(f"Total folders left to review: {total_folders}")
    print(f"Total files left to review: {total_files}\n")
    
    print("Breakdown by category:")
    for cat in sorted(counts.keys(), key=lambda x: counts[x], reverse=True):
        print(f"  - {cat}: {counts[cat]} bilder i {folder_counts.get(cat, 0)} mappar")

if __name__ == "__main__":
    main()
