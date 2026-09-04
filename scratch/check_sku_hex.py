import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')

with open(path, 'rb') as f:
    content = f.read()

# Let's search for "lucca-gr" in the raw bytes
pos = content.find(b"lucca-gr")
if pos != -1:
    start = max(0, pos - 40)
    end = pos + 40
    chunk = content[start:end]
    print("Chunk hex:", chunk.hex())
    print("Chunk repr:", chunk)
else:
    print("Pattern not found in bytes.")
