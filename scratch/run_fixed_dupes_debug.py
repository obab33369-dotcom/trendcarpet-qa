import sys
import os

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from test_fixed_resolver import fixed_resolve_anchor

print("=== DEBBUGING RESOLUTIONS ===")
for test_file in ["19787.jpg", "RG01-12.jpg", "matbord-hornstull-ek-svart.jpg"]:
    sku, name = fixed_resolve_anchor(test_file)
    print(f"File: {test_file} -> Resolved SKU: {sku} | Name: {name}")
