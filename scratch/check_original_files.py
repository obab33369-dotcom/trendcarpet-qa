import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def search_dir(directory, query):
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return []
    matches = []
    for f in os.listdir(directory):
        if query.lower() in f.lower():
            matches.append(os.path.join(directory, f))
    return matches

def main():
    dirs = [
        os.path.join(WORKSPACE_DIR, "reforma-original-images"),
        os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar")
    ]
    
    queries = ["2010001196273", "100519", "vaddo", "vadd", "vestby"]
    
    for d in dirs:
        print(f"\nScanning directory: {d}")
        for q in queries:
            matches = search_dir(d, q)
            print(f"  Query '{q}': found {len(matches)} matches")
            for m in matches[:5]:
                print(f"    - {os.path.basename(m)}")

if __name__ == "__main__":
    main()
