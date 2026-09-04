import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

dashboard_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "turboflow_dashboard.html")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find all image files
    img_pattern = re.compile(r'([\w\-]+\.(?:png|jpg|jpeg|webp))', re.IGNORECASE)
    matches = img_pattern.findall(content)
    
    # Filter out common UI assets or icons if any
    unique_images = sorted(list(set(matches)))
    
    print(f"Total images found in dashboard: {len(matches)}")
    print(f"Total unique images: {len(unique_images)}")
    print("Sample images:")
    for img in unique_images[:20]:
        print(f"  - {img}")
else:
    print("turboflow_dashboard.html not found")
