import os

def main():
    root_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
    found = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if "AGJM5060" in f:
                found.append(os.path.join(root, f))
                
    print("=== SEARCH RESULTS ===")
    for path in found:
        print(path)
        
if __name__ == "__main__":
    main()
