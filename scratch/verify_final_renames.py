import os

def main():
    base_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides"
    
    processed_1500_dir = os.path.join(base_dir, "Batch 2 - Processed (1500x1500)")
    processed_orig_dir = os.path.join(base_dir, "Batch 2 - Processed (Original Size)")
    combined_dir = os.path.join(base_dir, "Batch 2 - Combined Folders")
    verification_dir = os.path.join(base_dir, "Batch 2 - Rotated Verification")
    
    files_1500 = sorted([f for f in os.listdir(processed_1500_dir) if f.lower().endswith('.jpg')])
    files_orig = sorted([f for f in os.listdir(processed_orig_dir) if f.lower().endswith('.jpg')])
    folders_combined = sorted([d for d in os.listdir(combined_dir) if os.path.isdir(os.path.join(combined_dir, d))])
    files_verification = sorted([f for f in os.listdir(verification_dir) if f.lower().endswith('.jpg')])
    
    print(f"Total files in Processed (1500x1500): {len(files_1500)}")
    print(f"Total files in Processed (Original Size): {len(files_orig)}")
    print(f"Total subfolders in Combined Folders: {len(folders_combined)}")
    print(f"Total files in Rotated Verification: {len(files_verification)}")
    
    # Check that they match
    codes_1500 = {f.split('-')[1].lower(): f.split('-')[0] for f in files_1500}
    codes_orig = {f.split('-')[1].lower(): f.split('-')[0] for f in files_orig}
    codes_combined = {f.split('-')[1].lower(): f.split('-')[0] for f in folders_combined}
    codes_verify = {f.split('-')[1].split('.')[0].lower(): f.split('-')[0] for f in files_verification}
    
    mismatches = []
    for code, num in codes_1500.items():
        if codes_orig.get(code) != num:
            mismatches.append(f"Orig size mismatch for {code}: 1500={num}, orig={codes_orig.get(code)}")
        if codes_combined.get(code) != num:
            mismatches.append(f"Combined mismatch for {code}: 1500={num}, combined={codes_combined.get(code)}")
        if codes_verify.get(code) != num:
            mismatches.append(f"Verification mismatch for {code}: 1500={num}, verification={codes_verify.get(code)}")
            
    if mismatches:
        print("\nMISMATCHES FOUND:")
        for m in mismatches:
            print(m)
    else:
        print("\nALL 100 COWHIDES ARE CONSISTENTLY RENAMED AND MATCH IN ALL DIRECTORIES!")

if __name__ == "__main__":
    main()
