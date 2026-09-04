import sys
import os

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from test_fixed_resolver import fixed_resolve_anchor

sku, name = fixed_resolve_anchor("19787.jpg")
print(f"Direct import resolution: SKU={sku} | Name={name}")
