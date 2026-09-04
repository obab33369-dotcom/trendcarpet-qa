import os
import glob
import numpy as np
from PIL import Image

temp_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b"
attached_files = [
    os.path.join(temp_dir, "media__1781672790934.jpg"),
    os.path.join(temp_dir, "media__1781672798256.jpg"),
    os.path.join(temp_dir, "media__1781672812381.jpg"),
    os.path.join(temp_dir, "media__1781672844850.jpg"),
    os.path.join(temp_dir, "media__1781672854213.jpg")
]

search_root = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
candidate_files = glob.glob(os.path.join(search_root, "**", "*.jpg"), recursive=True) + glob.glob(os.path.join(search_root, "**", "*.png"), recursive=True)

def get_normalized_image(path):
    img = Image.open(path).convert('RGB').resize((128, 128))
    return np.array(img, dtype=np.float32)

print("Loading attached images:")
attached_data = []
for f in attached_files:
    if os.path.exists(f):
        arr = get_normalized_image(f)
        attached_data.append((f, arr))
        print(f"  Loaded {os.path.basename(f)}")
    else:
        print(f"  {f} does not exist!")

print(f"\nSearching for exact pixel matches among {len(candidate_files)} files under {search_root}:")
matches = {f: [] for f in attached_files}
for cand in candidate_files:
    try:
        cand_arr = get_normalized_image(cand)
        for att_f, att_arr in attached_data:
            mse = np.mean((att_arr - cand_arr) ** 2)
            if mse < 50: # strict match
                matches[att_f].append((cand, mse))
    except Exception as e:
        pass

for att_f, cands in matches.items():
    print(f"\nMatches for {os.path.basename(att_f)}:")
    cands = sorted(cands, key=lambda x: x[1])
    for cand, mse in cands[:3]:
        print(f"  MSE {mse:.2f}: {cand}")
