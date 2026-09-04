import os
import fnmatch

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    print(f"Searching for files matching '002-architectural-digest-style-002.png' or similar in {TURBOFLOW_ROOT}...")
    
    exact_matches = []
    partial_matches = []
    
    # We will search for:
    # 1. Exact name: "002-architectural-digest-style-002.png" (or with .jpg, or styl-)
    # 2. Files starting with "002-" and containing "architectural-digest"
    
    for dirpath, dirnames, filenames in os.walk(TURBOFLOW_ROOT):
        for f in filenames:
            f_lower = f.lower()
            if "002-architectural-digest-style-002.png" in f_lower or "002-architectural-digest-styl-002.png" in f_lower:
                exact_matches.append(os.path.join(dirpath, f))
            elif f_lower.startswith("002-") or "style-002" in f_lower or "styl-002" in f_lower:
                # Let's filter to keep relevant ones
                if "architectural" in f_lower:
                    partial_matches.append(os.path.join(dirpath, f))
                    
    print(f"\nExact matches found: {len(exact_matches)}")
    for p in exact_matches:
        print(f"  - {p}")
        
    print(f"\nPartial/Related matches found: {len(partial_matches)}")
    for p in partial_matches[:20]:
        print(f"  - {p}")
    if len(partial_matches) > 20:
        print(f"  ... and {len(partial_matches) - 20} more.")

if __name__ == "__main__":
    main()
