import re
import os
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from execute_full_catalog_sorting import _resolve_anchor_raw, brand_keys, sku_map

ref = "RG01-86.jpg"
print(f"Resolving: {ref}")

ref_lower = ref.lower()

# Let's run a custom version of _resolve_anchor_raw that prints what matches
def trace_resolve(ref):
    m = re.match(r'^(\d+)_', ref)
    if m:
        prefix = m.group(1)
        for k, v in sku_map.items():
            if k.startswith(prefix + "_"):
                print("Matched numeric prefix!")
                return v['sku'], v.get('slug')

    cleaned = ref
    if cleaned.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
        cleaned = os.path.splitext(cleaned)[0]
    base = re.sub(r'^\d+_', '', cleaned)
    base = re.sub(r'-1-26u-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1-26u$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-26u$', '', base, flags=re.IGNORECASE)
    cleaned = base
    
    def normalize(name):
        text = name.lower()
        repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', '’': '', '`': '', '\'': ''}
        for char, rep in repl.items():
            text = text.replace(char, rep)
        text = re.sub(r'[^a-z0-9]', '', text)
        return text

    norm_c = normalize(cleaned)
    
    def get_simple_norm(norm_val):
        val = re.sub(r'\d+x\d+', '', norm_val)
        val = re.sub(r'\d+cm', '', val)
        val = re.sub(r'\d+', '', val)
        colors = ['cm', 'ek', 'valnot', 'svart', 'vit', 'gra', 'natur', 'beige', 'gron', 'bla', 'morkgra', 'ljusgra', 'brun', 'guld', 'massing', 'silver', 'satin', 'creme']
        for color in colors:
            val = val.replace(color, '')
        return val

    simple_norm_c = get_simple_norm(norm_c)
    
    print(f"cleaned: {cleaned}, norm_c: {norm_c}, simple_norm_c: {simple_norm_c}")

    for bk in brand_keys:
        if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
            print("Matched norm_slug == norm_c!")
            return bk['sku'], bk['name']

    for bk in brand_keys:
        if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
            print("Matched simple_norm_slug == simple_norm_c!")
            return bk['sku'], bk['name']

    for bk in brand_keys:
        # Check if norm_c is in norm_slug or vice versa
        cond1 = bk['norm_slug'] in norm_c
        cond2 = norm_c in bk['norm_slug']
        cond3 = bk['norm_name'] in norm_c
        cond4 = norm_c in bk['norm_name']
        if cond1 or cond2 or cond3 or cond4:
            print(f"Matched substring check! cond1={cond1}, cond2={cond2}, cond3={cond3}, cond4={cond4}")
            print(f"BK: slug={bk['slug']}, name={bk['name']}, norm_slug={bk['norm_slug']}, norm_name={bk['norm_name']}")
            return bk['sku'], bk['name']

    for bk in brand_keys:
        cond1 = bk['simple_norm_slug'] in simple_norm_c
        cond2 = simple_norm_c in bk['simple_norm_slug']
        cond3 = bk['simple_norm_name'] in simple_norm_c
        cond4 = simple_norm_c in bk['simple_norm_name']
        if cond1 or cond2 or cond3 or cond4:
            if len(bk['simple_norm_slug']) > 4 or len(bk['simple_norm_name']) > 4:
                print("Matched simple substring check!")
                return bk['sku'], bk['name']

    return None, None

sku, name = trace_resolve(ref)
print(f"Resolved to SKU: {sku} | Name: {name}")
