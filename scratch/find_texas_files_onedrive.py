import os
import glob
import re

PROJECT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

target_prefixes = [17, 18, 23, 24, 87, 88, 145, 146, 351, 352, 369, 370, 423, 424, 461, 462, 555, 556, 567, 568]

found = []
for src_dir in [os.path.join(PROJECT_DIR, "första omgången fyrkantiga"), PROJECT_DIR]:
    if not os.path.exists(src_dir):
        continue
    for f in os.listdir(src_dir):
        if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
        # Parse prefix
        m = re.match(r"^(\d+)", f)
        if m:
            prefix = int(m.group(1))
            if prefix in target_prefixes:
                found.append((prefix, f, os.path.join(src_dir, f)))

print(f"Found {len(found)} files matching Texas Sofa indices from Batch 2:")
for prefix, filename, path in sorted(found, key=lambda x: x[0]):
    # Parse suffix
    m_style = re.search(r"-styl(?:e)?-(\d+)([a-z])?$", os.path.splitext(filename)[0], re.IGNORECASE)
    suffix = int(m_style.group(1)) if m_style else None
    diff = prefix - suffix if suffix is not None else 0
    print(f"Prefix: {prefix:03d} | Suffix: {suffix} | Diff: {diff} | File: {filename}")
