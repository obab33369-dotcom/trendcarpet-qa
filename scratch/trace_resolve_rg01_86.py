import re
import os
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from execute_full_catalog_sorting import sku_map, brand_keys, get_beautiful_name, clean_ref, normalize, get_simple_norm

ref = "RG01-86.jpg"
print(f"Tracing resolution for '{ref}'")

ref_lower = ref.lower()

# Line 121
m = re.match(r'^(\d+)_', ref)
if m:
    print("Match 1: Numeric prefix")
else:
    print("No Match 1: Numeric prefix")

# Line 152
if ref in sku_map:
    print("Match 2: In sku_map")
else:
    print("No Match 2: In sku_map")

# Line 161
found_lc = False
for k, v in sku_map.items():
    if k.lower() == ref.lower():
        print(f"Match 3: Case-insensitive sku_map lookup: {k}")
        found_lc = True
if not found_lc:
    print("No Match 3: Case-insensitive sku_map lookup")

# Line 170
cleaned = clean_ref(ref)
norm_c = normalize(cleaned)
simple_norm_c = get_simple_norm(norm_c)
print(f"Cleaned: '{cleaned}' | Normalized: '{norm_c}' | Simple Normalized: '{simple_norm_c}'")

# Line 174
found_bk_direct = False
for bk in brand_keys:
    if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
        print(f"Match 4: bk direct match: {bk['sku']}")
        found_bk_direct = True
if not found_bk_direct:
    print("No Match 4: bk direct match")

# Line 178
if re.match(r'^\d+$', cleaned):
    print("Match 5: Cleaned is digit")
else:
    print("No Match 5: Cleaned is digit")

# Line 188
found_bk_simple = False
for bk in brand_keys:
    if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
        print(f"Match 6: bk simple match: {bk['sku']} | Slug: {bk['slug']}")
        found_bk_simple = True
if not found_bk_simple:
    print("No Match 6: bk simple match")

# Line 192
found_bk_substring = False
for bk in brand_keys:
    if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
        print(f"Match 7: bk substring match: {bk['sku']} | Name: {bk['name']}")
        found_bk_substring = True
        break # In the original function it returns immediately here!
