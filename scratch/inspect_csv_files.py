import os
import glob

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

csv_files = glob.glob(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "*.csv"))
print(f"Found {len(csv_files)} CSV files in reforma-turboflow:")
for csv_path in csv_files:
    print(f"\n--- File: {os.path.basename(csv_path)} ---")
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            for i in range(5):
                line = f.readline()
                if not line:
                    break
                print(line.strip())
    except Exception as e:
        print(f"Error reading: {e}")
