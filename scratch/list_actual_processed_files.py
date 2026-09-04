import os

def main():
    processed_1500_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides\Batch 2 - Processed (1500x1500)"
    processed_orig_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-10-cowhides\Batch 2 - Processed (Original Size)"
    
    files_1500 = sorted([f for f in os.listdir(processed_1500_dir) if f.lower().endswith('.jpg')])
    files_orig = sorted([f for f in os.listdir(processed_orig_dir) if f.lower().endswith('.jpg')])
    
    print(f"Total files in Processed (1500x1500): {len(files_1500)}")
    print("Files (first 10):", files_1500[:10])
    print("Files (last 10):", files_1500[-10:])
    
    print(f"\nTotal files in Processed (Original Size): {len(files_orig)}")
    
    # Are there any files that don't start with a number?
    unrenamed_1500 = [f for f in files_1500 if not f.split('-')[0].isdigit()]
    print(f"\nUnrenamed in Processed (1500x1500) ({len(unrenamed_1500)} files):")
    print(unrenamed_1500)
    
    unrenamed_orig = [f for f in files_orig if not f.split('-')[0].isdigit()]
    print(f"\nUnrenamed in Processed (Original Size) ({len(unrenamed_orig)} files):")
    print(unrenamed_orig)

if __name__ == "__main__":
    main()
