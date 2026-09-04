import json
import os
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from execute_full_catalog_sorting import _resolve_anchor_raw, sku_map, brand_keys

ref = "RG01-86.jpg"
sku, name = _resolve_anchor_raw(ref)
print(f"Resolving '{ref}' -> SKU: {sku} | Name: {name}")

# Let's trace how it matches
print("\nTracing matches in brand_keys...")
cleaned = ref
if cleaned.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
    cleaned = os.path.splitext(cleaned)[0]
# From clean_ref
import re
base = re.sub(r'^\d+_', '', cleaned)
base = re.sub(r'-1-26u-wonder$', '', base, flags=re.IGNORECASE)
base = re.sub(r'-1-26u$', '', base, flags=re.IGNORECASE)
base = re.sub(r'-wonder$', '', base, flags=re.IGNORECASE)
base = re.sub(r'-1$', '', base, flags=re.IGNORECASE)
base = re.sub(r'-26u$', '', base, flags=re.IGNORECASE)
cleaned = base

print(f"Cleaned ref: {cleaned}")
# normalize
def normalize(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', '’': '', '`': '', '\'': ''}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

norm_c = normalize(cleaned)
print(f"Normalized ref: {norm_c}")

# Let's see if any brand_key norm_slug or norm_name matches norm_c
for bk in brand_keys:
    if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
        print(f"Direct match found: Slug: {bk['slug']} | Name: {bk['name']} | SKU: {bk['sku']}")

# Let's search brand_keys for SKU == 'advent-star-white-10' or 'RG01-86'
print("\nSearching brand_keys by SKU...")
for bk in brand_keys:
    if bk['sku'] == 'advent-star-white-10' or bk['sku'] == 'RG01-86':
        print(f"BK: Slug: {bk['slug']} | SKU: {bk['sku']} | Name: {bk['name']} | norm_slug: {bk['norm_slug']} | norm_name: {bk['norm_name']}")
