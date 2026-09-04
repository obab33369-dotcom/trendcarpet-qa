import os
import sys
import fnmatch
import datetime

TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

def main():
    if len(sys.argv) < 2:
        print("Usage: python scratch/search_turboflow.py <search_term_or_pattern>")
        print("Example: python scratch/search_turboflow.py 002-architectural")
        print("Example: python scratch/search_turboflow.py *002*")
        return
        
    query = sys.argv[1].strip()
    query_lower = query.lower()
    
    print("=" * 80)
    print(f"SEARCHING FOR: '{query}' in {TURBOFLOW_ROOT}")
    print("=" * 80)
    
    is_glob = any(char in query for char in ["*", "?", "[", "]"])
    
    matches = []
    
    for dirpath, dirnames, filenames in os.walk(TURBOFLOW_ROOT):
        # We can search in directory names as well if helpful, but usually filenames
        for f in filenames:
            matched = False
            if is_glob:
                if fnmatch.fnmatch(f.lower(), query_lower):
                    matched = True
            else:
                if query_lower in f.lower():
                    matched = True
                    
            if matched:
                full_path = os.path.join(dirpath, f)
                try:
                    stat = os.stat(full_path)
                    size_kb = stat.st_size / 1024.0
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                    matches.append((f, size_kb, mtime, full_path))
                except Exception:
                    matches.append((f, 0, None, full_path))
                    
    if not matches:
        print("No matches found.")
        return
        
    print(f"Found {len(matches)} matching files:")
    print("-" * 80)
    
    # Sort matches by directory and filename
    matches.sort(key=lambda x: (os.path.dirname(x[3]), x[0]))
    
    for idx, (fname, size, mtime, path) in enumerate(matches):
        rel_dir = os.path.relpath(os.path.dirname(path), TURBOFLOW_ROOT)
        mtime_str = mtime.strftime("%Y-%m-%d %H:%M") if mtime else "Unknown"
        print(f"[{idx+1}] File: {fname}")
        print(f"    Folder: {rel_dir}")
        print(f"    Size:   {size:.1f} KB  |  Modified: {mtime_str}")
        print(f"    Path:   {path}")
        print("-" * 80)

if __name__ == "__main__":
    main()
