import re

with open("rugs_snippet.html", "r", encoding="utf-8") as f:
    snippet = f.read()

# Look for links that point to product pages or images
links = re.findall(r'href="([^"]+)"', snippet)
print(f"Total hrefs in first 100k: {len(links)}")
for l in list(set(links))[:30]:
    print(f"  - {l}")

print("\n--- Testing image lazy-loading patterns ---")
data_srcs = re.findall(r'data-src="([^"]+)"', snippet)
print(f"Found {len(data_srcs)} data-src attributes.")
for ds in data_srcs[:10]:
    print(f"  - {ds}")

# Read entire HTML to find all product images
with open("C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\rugs_snippet.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's find any data-src containing 'artiklar' or 'images' or 'products'
data_src_products = re.findall(r'data-src="([^"]+)"', html)
print(f"\nFound {len(data_src_products)} data-src images.")
for dsp in data_src_products[:20]:
    print(f"  - {dsp}")

# Let's search for image sources inside picture or img tags with lazy loading
img_tags = re.findall(r'<img [^>]+>', html)
print(f"\nFound {len(img_tags)} img tags.")
for img in img_tags[:10]:
    print(f"  - {img}")
