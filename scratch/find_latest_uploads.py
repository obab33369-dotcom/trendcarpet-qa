import os
import time

def main():
    root_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\1f2e7c2f-067a-4ff4-9fab-d8c23eca771c"
    now = time.time()
    found = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            path = os.path.join(root, f)
            mtime = os.path.getmtime(path)
            # Files modified in the last 15 minutes (900 seconds)
            if now - mtime < 900:
                found.append((path, mtime))
                
    found = sorted(found, key=lambda x: x[1], reverse=True)
    print("=== RECENTLY MODIFIED FILES ===")
    for path, mtime in found:
        print(f"{path} (modified: {time.ctime(mtime)}, size: {os.path.getsize(path)} bytes)")

if __name__ == "__main__":
    main()
