import os
import json

def main():
    base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides"
    processed_1500_dir = os.path.join(base_dir, "Batch 2 - Processed (1500x1500)")
    processed_orig_dir = os.path.join(base_dir, "Batch 2 - Processed (Original Size)")
    combined_dir = os.path.join(base_dir, "Batch 2 - Combined Folders")
    verification_dir = os.path.join(base_dir, "Batch 2 - Rotated Verification")
    
    final_json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\cowhide_numbers_final.json"
    
    if not os.path.exists(final_json_path):
        print("Final JSON database not found.")
        return
        
    with open(final_json_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    print(f"Total files in JSON database: {len(db)}")
    
    # Check frequencies
    counts = {}
    for filename, info in db.items():
        num = info.get("number")
        counts[num] = counts.get(num, []) + [filename]
        
    print("\n=== FINAL NUMBER FREQUENCIES ===")
    duplicates = {}
    for num, files in sorted(counts.items()):
        print(f"Number {num}: {files}")
        if len(files) > 1:
            duplicates[num] = files
            
    print(f"\nDuplicates found: {len(duplicates)}")
    
    # Check files on disk
    files_1500 = sorted([f for f in os.listdir(processed_1500_dir) if f.lower().endswith('.jpg')])
    files_orig = sorted([f for f in os.listdir(processed_orig_dir) if f.lower().endswith('.jpg')])
    folders_combined = sorted([d for d in os.listdir(combined_dir) if os.path.isdir(os.path.join(combined_dir, d))])
    files_verification = sorted([f for f in os.listdir(verification_dir) if f.lower().endswith('.jpg')])
    
    print(f"\nFiles on disk:")
    print(f"  - Processed (1500x1500): {len(files_1500)}")
    print(f"  - Processed (Original Size): {len(files_orig)}")
    print(f"  - Combined Folders: {len(folders_combined)}")
    print(f"  - Rotated Verification: {len(files_verification)}")
    
    mismatches = []
    codes_1500 = {f.split('-')[1].lower(): f.split('-')[0] for f in files_1500}
    codes_orig = {f.split('-')[1].lower(): f.split('-')[0] for f in files_orig}
    codes_combined = {f.split('-')[1].lower(): f.split('-')[0] for f in folders_combined}
    codes_verify = {f.split('-')[1].split('.')[0].lower(): f.split('-')[0] for f in files_verification}
    
    for filename, info in db.items():
        code = filename.split('.')[0].lower()
        num = info.get("number")
        
        if codes_1500.get(code) != num:
            mismatches.append(f"Processed 1500 mismatch for {code}: expected={num}, found={codes_1500.get(code)}")
        if codes_orig.get(code) != num:
            mismatches.append(f"Processed Original Size mismatch for {code}: expected={num}, found={codes_orig.get(code)}")
        if codes_combined.get(code) != num:
            mismatches.append(f"Combined Folder mismatch for {code}: expected={num}, found={codes_combined.get(code)}")
        if codes_verify.get(code) != num:
            mismatches.append(f"Verification mismatch for {code}: expected={num}, found={codes_verify.get(code)}")
            
    if mismatches:
        print("\nMISMATCHES FOUND ON DISK:")
        for m in mismatches[:10]:
            print("  -", m)
        if len(mismatches) > 10:
            print(f"  - ... and {len(mismatches)-10} more.")
    else:
        print("\nALL FILES ON DISK REFLECT THE UPDATED NUMBERS PERFECTLY WITH NO MISMATCHES!")

if __name__ == "__main__":
    main()
