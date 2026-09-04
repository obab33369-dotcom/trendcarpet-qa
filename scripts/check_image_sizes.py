import os
from PIL import Image

PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

print("Checking dimensions of some renders in OneDrive...")
renders = [f for f in os.listdir(PICS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
for f in renders[:5]:
    path = os.path.join(PICS_DIR, f)
    with Image.open(path) as img:
        print(f"  Render '{f}': Size = {img.size} ({img.width/img.height:.3f} AR)")

# Check some webp reference images
TEST_FURNITURE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_furniture"
print("\nChecking dimensions of some original reference webp files...")
if os.path.exists(TEST_FURNITURE_DIR):
    refs = [f for f in os.listdir(TEST_FURNITURE_DIR) if f.lower().endswith('.webp')]
    for f in refs[:5]:
        path = os.path.join(TEST_FURNITURE_DIR, f)
        with Image.open(path) as img:
            print(f"  Reference '{f}': Size = {img.size} ({img.width/img.height:.3f} AR)")
else:
    print("test_furniture folder not found")
